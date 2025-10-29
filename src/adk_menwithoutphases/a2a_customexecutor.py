from a2a.types import AgentCard
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


# The Agent Executor is the heart of the agent's runtime logic.
# It defines how the agent processes incoming requests, interacts with its runner,
# and generates responses or events.
class MenWithoutPhasesAgentExecutor(AgentExecutor):
    def __init__(self, agent: Agent, agent_card: AgentCard, runner: Runner):
        # Initialize the executor with the agent, its card, and the ADK runner.
        self.agent = agent
        self.runner = runner  # Runner's are the central component responsible for executing your ADK agents
        self.agent_card = agent_card
        self.session_service = self.runner.session_service

    # This gets the necessary information from the request context, performs the necessary operations, 
    # and then publishes a Message or Task onto the EventQueue
    # The `execute` method is the main entry point for processing an incoming request.
    async def execute(self, request_context: RequestContext, event_queue: EventQueue,) -> None:
        try:
            # Inspect the metadata of the request to extract relevant IDs.
            task_id = request_context.task_id or "default_task_id"
            context_id = request_context.context_id or "default_context_id"
            user_id = "self" # setting a default 

            logging.info(f"The context id is {context_id}")
            logging.info(f"The task id is {task_id}")
            
            # Ensure an ADK session exists for the user and context.
            await self._get_adk_session(user_id, context_id)
            
            # Extract the user's message from the request context.
            user_message = self._inspect_input(request_context)

            # Process the user message through the underlying LLM agent.
            message_text = await self._run_agent(user_message, event_queue, user_id, context_id)

            # Send message back to calling agent
            await self._send_response(event_queue, request_context, message_text)

        except Exception as error:
            self._handle_error(event_queue, request_context, error)

    # Runs the ADK agent with the user's message and processes the events.
    async def _run_agent(self, user_message: str, event_queue: EventQueue, user_id: str, session_id: str) -> str:
        # Create a Content object for the user's message.
        message_content = types.Content(role="user", parts=[types.Part(text=user_message)])
    
        logger.debug(f"Running ADK agent {self.agent.name} with session {session_id}")

        # `run_async` executes the agent and yields events as they occur.
        events_async = self.runner.run_async(
            user_id=user_id, session_id=session_id, new_message=message_content
        )

        # Initialize a default response in case no final response is found.
        final_message_text = "(No search results found)"

        async for event in events_async:
            if (
                event.is_final_response()
                and event.content
                and event.content.role == "model"
            ):
                # If a final model response is received, extract the text.
                if event.content.parts and event.content.parts[0].text:
                    final_message_text = event.content.parts[0].text
                    logger.info(
                        f"{self.agent.name} final response: '{final_message_text[:200]}{'...' if len(final_message_text) > 200 else ''}'"
                    )
                    break
                else:
                    # Log a warning if the final event has no text content.
                    logger.warning(
                        f"{self.agent.name} received final event but no text in first part: {event.content.parts}"
                    )
            elif event.is_final_response():
                # Log a warning if the final event lacks model content.
                logger.warning(
                    f"{self.agent.name} received final event without model content: {event}"
                )
            else:
                # Log a warning for any non-final events that are not explicitly handled.
                logger.warning(
                    f"{self.agent.name} received final non-final event: {event}"
                )

        return final_message_text

    
    # Handles cancellation requests for a given task.
    async def cancel(self, request_context: RequestContext, event_queue: EventQueue):
        context_id = request_context.context_id or "default_context_id"
        user_id = "self"  # setting a default

        logging.info(f"Canceling task with context_id: {context_id}")

        # Delete the session associated with the canceled task.
        await self.session_service.delete_session(
            app_name=self.runner.app_name, user_id=user_id, session_id=context_id
        )

        logging.info(f"Canceled task with context_id: {context_id}")


    # Extracts the user's input message from the request context.
    def _inspect_input(self, request_context: RequestContext) -> str:
        user_message = request_context.get_user_input()
        logging.info(f"The user message is: {user_message}")
        return user_message

    # Retrieves an existing ADK session or creates a new one if it doesn't exist.
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

    # Handles errors during agent execution and sends an error message back.
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
