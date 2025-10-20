from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.utils import new_agent_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext 
from a2a.server.events import EventQueue
from google.adk.sessions import Session
from google.adk.runners import Runner
from google.adk.agents import Agent
from google.genai import types

import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# The Agent Card

capabilities = AgentCapabilities(streaming=False, tools=True)

agent_card = AgentCard(
    name="men_without_faces_agent",
    description="Clandestine agent for the `Men without Faces` organization.",
    skills=[
        AgentSkill(
            name="arrange_discreet_service",
            id ="discreet_services",
            description="Arranges discreet and clandestine services that are not directly acknowledged by the Metal Bank.",
            tags=[]
        ),
        AgentSkill(
            name="men_without_faces_discuss_price",
            id ="discuss_price",
            description="Negotiate prices for the services offered by the `Men without Faces` organization.",
            tags=[]
        ),
    ],
    capabilities=capabilities,
    url=f'http://localhost:{os.environ.get("PORT", 8001)}',
    version="0.1.0",
    default_input_modes=["text"],
    default_output_modes=["text"]
)   

# The Agent Executor
# This is where the core logic of how the agent processes requests and generates responses/events lives.

class MenWithoutFacesAgentExecutor(AgentExecutor):
    def __init__(self, agent: Agent, agent_card: AgentCard, runner: Runner):
        self.agent = agent
        self.runner = runner  # Runner's are the central component responsible for executing your ADK agents
        self.agent_card = agent_card
        self.session_service = self.runner.session_service


    async def execute(self, request_context: RequestContext, event_queue: EventQueue,) -> None:
        try:
            # This gets the necessary information from the request context, performs the necessary operations, 
            # and then publishes a Message or Task onto the EventQueue

            # Lets inspect the metadata of the request. 
            task_id = request_context.task_id or "default_task_id"
            context_id = request_context.context_id or "default_context_id"
            user_id = "self" # setting a default 

            logging.info(f"The context id is {context_id}")
            logging.info(f"The task id is {task_id}")

            await self._get_adk_session(user_id, context_id)
            
            # Let's inspect the user input
            user_message = self._inspect_input(request_context)

            # Do some processing on the user message through the Agent
            message_text = await self._run_agent(user_message, event_queue, user_id, context_id)

            # Send message back to calling agent
            await self._send_response(event_queue, request_context, message_text)

        except Exception as error:
            self._handle_error(event_queue, request_context, error)

    async def _run_agent(self, user_message: str, event_queue: EventQueue, user_id: str, session_id: str) -> str:
        message_content = types.Content(role="user", parts=[types.Part(text=user_message)])
    
        logger.debug(f"Running ADK agent {self.agent.name} with session {session_id}")

        # The runner emits events as it continues to process the user's request
        events_async = self.runner.run_async(
            user_id=user_id, session_id=session_id, new_message=message_content
        )

        final_message_text = "(No search results found)"

        async for event in events_async:
            if (
                event.is_final_response()
                and event.content
                and event.content.role == "model"
            ):
                if event.content.parts and event.content.parts[0].text:
                    final_message_text = event.content.parts[0].text
                    logger.info(
                        f"{self.agent.name} final response: '{final_message_text[:200]}{'...' if len(final_message_text) > 200 else ''}'"
                    )
                    break
                else:
                    logger.warning(
                        f"{self.agent.name} received final event but no text in first part: {event.content.parts}"
                    )
            elif event.is_final_response():
                logger.warning(
                    f"{self.agent.name} received final event without model content: {event}"
                )
            else:
                logger.warning(
                    f"{self.agent.name} received final non-final event: {event}"
                )

        return final_message_text

    
    async def cancel(self, request_context: RequestContext, event_queue: EventQueue):
        context_id = request_context.context_id or "default_context_id"
        user_id = "self"  # setting a default

        logging.info(f"Canceling task with context_id: {context_id}")

        await self.session_service.delete_session(
            app_name=self.runner.app_name, user_id=user_id, session_id=context_id
        )

        logging.info(f"Canceled task with context_id: {context_id}")


    def _inspect_input(self, request_context: RequestContext) -> str:
        user_message = request_context.get_user_input()
        logging.info(f"The user message is: {user_message}")
        return user_message

    async def _get_adk_session(self, user_id: str, session_id: str) -> None:
        """Retrieve an ADK session or create a new one if it doesn't exist."""
        adk_session: Session | None = await self.session_service.get_session(
            app_name=self.runner.app_name, user_id=user_id, session_id=session_id
        )
        if not adk_session:
            await self.session_service.create_session(
                app_name=self.runner.app_name,
                user_id=user_id,
                session_id=session_id,
                state={},
            )
            logger.info(f"Created new ADK session: {session_id} for {self.agent.name}")

    
    async def _send_response(
        self, event_queue: EventQueue, context: RequestContext, message_text: str
    ) -> None:
        """Send the response back via the event queue."""
        logger.info(f"Sending response for task {context.task_id}")
        await event_queue.enqueue_event(
            new_agent_text_message(
                text=message_text,
                context_id=context.context_id,
                task_id=context.task_id,
            )
        )

    def _handle_error(
        self,
        event_queue: EventQueue,
        context: RequestContext,
        error: Exception,
    ) -> None:
        """Handle errors and send error response."""
        logger.error(
            f"Error speaking to Men without Faces agent: {str(error)}",
            exc_info=True,
        )
        error_message_text = f"Error speaking to Men without Faces agent: {str(error)}"
        event_queue.enqueue_event(
            new_agent_text_message(
                text=error_message_text,
                context_id=context.context_id,
                task_id=context.task_id,
            )
        )
