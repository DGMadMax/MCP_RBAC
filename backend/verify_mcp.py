
import json
import urllib.request
import urllib.error

def verify_mcp():
    # Note: Added trailing slash to avoid 307 Redirect
    url = "http://localhost:8000/mcp/"
    data = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "query_database",
            "arguments": {
                "query": "How many employees are there in total?",
                "user_role": "admin",
                "user_id": 1
            }
        },
        "id": 1
    }
    
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'), 
        headers=headers, 
        method='POST'
    )
    
    try:
        print(f"Sending request to {url}...")
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print(f"Response status: {response.status}")
            print("Response body:")
            print(result)
            
            # Basic validation
            if "error" in result.lower() and "result" not in result:
                print("\n[FAILED] Error in response")
            elif "50" in result or "query" in result.lower():
                print("\n[SUCCESS] Returned data!")
            else:
                print("\n[UNCERTAIN] Check the output above")
                
    except urllib.error.URLError as e:
        print(f"[FAILED] Connection failed: {e}")
        print("Is the backend server running on port 8000?")

if __name__ == "__main__":
    verify_mcp()
