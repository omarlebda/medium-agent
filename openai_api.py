import json
from datetime import datetime
import time

from openai import OpenAI, NotFoundError

import config
from mongodb_api import create_thread, get_thread
from utils import save_request

client = OpenAI(
    api_key=config.OPENAI_API_KEY
)

def handle_tool_call(tool_call):
    """Handle different tool calls based on function name"""
    function_name = tool_call.function.name
    params = json.loads(tool_call.function.arguments)
    print(f"params: {params}")
    result = {"success": "false"}
    
    try:
        if function_name == "save_request":
            # Extract all parameters individually
            request_data = params.get("request_data", {})
            # Extract individual fields from 'request_data'
            name = request_data.get("name", "")
            request_type = request_data.get("type", "")
            sender_email = request_data.get("from", "")
            reply = request_data.get("reply", "")
            subject = request_data.get("subject", "")
            act_as_type = request_data.get("actAsType", "")
            message = request_data.get("message", "")
            
            # Create a structured request_data dictionary
            request_data = {
                "name": name,
                "type": "2",
                "from": sender_email,
                "reply": reply,
                "subject": subject,
                "actAsType": "customer",
                "message": message
            }
            print(f"Request data: {request_data}")
            # Call the save_request function
            success = save_request(request_data)
            result = {"success": str(success).lower()}
        
        print(f"Tool call {function_name} result: {result}")
        return result
        
    except Exception as e:
        print(f"Error in {function_name}: {str(e)}")
        return {"success": "false", "error": str(e)}

def ask_openai_assistant(query: str, recipient_id: str, messages: list[dict[str, str]]) -> str:
    try:
        # Retrieve or create a thread
        thread_from_db = get_thread(recipient_id=recipient_id)
        thread = None
        if thread_from_db:
            try:
                thread = client.beta.threads.retrieve(
                    thread_id=thread_from_db["thread_id"]
                )
            except NotFoundError as ne:
                print(ne.message)
                thread = client.beta.threads.create(
                    messages=messages
                )
        else:
            thread = client.beta.threads.create(
                messages=messages
            )
            thread_for_db = {
                'created_at': datetime.now().isoformat(),
                "thread_id": thread.id,
                "recipient_id": recipient_id
            }
            create_thread(thread=thread_for_db)
        print(f"Thread ID: {thread.id}")
        
        # Check for active runs
        active_run = None
        try:
            active_run = client.beta.threads.runs.list(thread_id=thread.id).data[0]
            if active_run.status not in ['completed', 'failed']:
                print(f"Active run found: {active_run.id}, waiting for completion.")
                while active_run.status not in ['completed', 'failed']:
                    time.sleep(1)
                    active_run = client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=active_run.id
                    )
        except IndexError:
            # No active runs, safe to proceed
            pass
        
        # Add user message to the thread
        _ = client.beta.threads.messages.create(
            thread_id=thread.id,
            content=query,
            role='user'
        )
        
        # Start a new assistant run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=config.ASSISTANT_ID
        )
        print(f"Run ID: {run.id}")
        
        # Poll the run until completion
        flag = True
        while flag:
            retrieved_run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if retrieved_run.required_action and retrieved_run.required_action.submit_tool_outputs:
                print("Function calls detected:")
                tool_outputs = []
                
                for tool_call in retrieved_run.required_action.submit_tool_outputs.tool_calls:
                    print(f"\nProcessing tool call:")
                    print(f"Function: {tool_call.function.name}")
                    print(f"Arguments: {tool_call.function.arguments}")
                    
                    # Handle the tool call
                    result = handle_tool_call(tool_call)
                    
                    # Add the result to tool outputs
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })

                # Submit all tool outputs
                if tool_outputs:
                    try:
                        run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                            thread_id=thread.id,
                            run_id=run.id,
                            tool_outputs=tool_outputs
                        )
                        print("Tool outputs submitted successfully")
                    except Exception as e:
                        print(f"Failed to submit tool outputs: {e}")
            
            if retrieved_run.status == 'completed':
                flag = False
            elif retrieved_run.status == 'failed':
                return config.ERROR_MESSAGE
            
            time.sleep(1)
        
        # Retrieve and return the first message content
        retrieved_messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        print(f"First Message: {retrieved_messages.data[0]}")
        message_text = retrieved_messages.data[0].content[0].text.value
        return message_text
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return config.ERROR_MESSAGE
