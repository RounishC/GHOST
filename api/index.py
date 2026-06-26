import json

def handler(request):
    """Vercel Serverless Function Handler"""
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'}
        }
    
    path = request.path
    
    if path == '/' or path == '':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"message": "GHOST Route Planner", "status": "ok"})
        }
    elif path == '/api/health':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"status": "healthy"})
        }
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "not found"})
        }


# For WSGI compatibility
app = handler


