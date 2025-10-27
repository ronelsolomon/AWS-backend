import os
import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import BaseModel, validator
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize utilities
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

# Pydantic Models for request/response validation
class ItemCreate(BaseModel):
    name: str
    description: str

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ResponseModel(BaseModel):
    statusCode: int
    body: str
    headers: Dict[str, str] = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

# Utility functions
def get_user_id(event: Dict[str, Any]) -> str:
    """Extract user ID from Cognito JWT token"""
    try:
        return event['requestContext']['authorizer']['claims']['sub']
    except (KeyError, TypeError) as e:
        logger.error(f"Error extracting user ID: {str(e)}")
        raise ValueError("Invalid authorization token")

def build_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Build API Gateway response"""
    return {
        'statusCode': status_code,
        'body': json.dumps(body, default=str),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }

# Lambda handler
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Main Lambda handler for the API Gateway
    """
    try:
        http_method = event['httpMethod']
        path = event['resource']
        
        # Route the request
        if http_method == 'GET' and path == '/items':
            return list_items(event)
        elif http_method == 'POST' and path == '/items':
            return create_item(event)
        elif http_method == 'GET' and path.startswith('/items/'):
            return get_item(event)
        elif http_method == 'PUT' and path.startswith('/items/'):
            return update_item(event)
        elif http_method == 'DELETE' and path.startswith('/items/'):
            return delete_item(event)
        else:
            return build_response(404, {'message': 'Not Found'})
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return build_response(500, {'message': 'Internal Server Error'})

# CRUD Operations
def list_items(event: Dict[str, Any]) -> Dict[str, Any]:
    """List all items for the authenticated user"""
    try:
        user_id = get_user_id(event)
        
        response = table.query(
            IndexName='user-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        return build_response(200, {
            'items': response.get('Items', [])
        })
        
    except Exception as e:
        logger.error(f"Error listing items: {str(e)}")
        return build_response(500, {'message': 'Failed to list items'})

def create_item(event: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new item"""
    try:
        user_id = get_user_id(event)
        request_body = json.loads(event['body'])
        
        # Validate input
        item_data = ItemCreate(**request_body)
        
        # Generate item ID and timestamps
        item_id = context.aws_request_id
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare item
        item = {
            'id': item_id,
            'user_id': user_id,
            'created_at': timestamp,
            'updated_at': timestamp,
            **item_data.dict()
        }
        
        # Save to DynamoDB
        table.put_item(Item=item)
        
        return build_response(201, item)
        
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        return build_response(500, {'message': 'Failed to create item'})

def get_item(event: Dict[str, Any]) -> Dict[str, Any]:
    """Get a single item by ID"""
    try:
        user_id = get_user_id(event)
        item_id = event['pathParameters']['id']
        
        # Get item from DynamoDB
        response = table.get_item(
            Key={'id': item_id}
        )
        
        item = response.get('Item')
        if not item:
            return build_response(404, {'message': 'Item not found'})
            
        # Ensure the user owns this item
        if item.get('user_id') != user_id:
            return build_response(403, {'message': 'Forbidden'})
            
        return build_response(200, item)
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return build_response(500, {'message': 'Error retrieving item'})
    except Exception as e:
        logger.error(f"Error getting item: {str(e)}")
        return build_response(500, {'message': 'Internal server error'})

def update_item(event: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing item"""
    try:
        user_id = get_user_id(event)
        item_id = event['pathParameters']['id']
        request_body = json.loads(event['body'])
        
        # Validate input
        update_data = ItemUpdate(**request_body).dict(exclude_unset=True)
        
        if not update_data:
            return build_response(400, {'message': 'No valid fields to update'})
        
        # Prepare update expression
        update_expression = []
        expression_attribute_values = {}
        
        for key, value in update_data.items():
            update_expression.append(f"{key} = :{key}")
            expression_attribute_values[f":{key}"] = value
        
        # Add updated_at timestamp
        update_expression.append("updated_at = :updated_at")
        expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()
        
        # Update item in DynamoDB
        response = table.update_item(
            Key={'id': item_id},
            UpdateExpression="SET " + ", ".join(update_expression),
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={
                **expression_attribute_values,
                ":user_id": user_id
            },
            ReturnValues="ALL_NEW"
        )
        
        return build_response(200, response['Attributes'])
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return build_response(403, {'message': 'Forbidden'})
        logger.error(f"DynamoDB error: {str(e)}")
        return build_response(500, {'message': 'Error updating item'})
    except Exception as e:
        logger.error(f"Error updating item: {str(e)}")
        return build_response(500, {'message': 'Internal server error'})

def delete_item(event: Dict[str, Any]) -> Dict[str, Any]:
    """Delete an item"""
    try:
        user_id = get_user_id(event)
        item_id = event['pathParameters']['id']
        
        # Delete item from DynamoDB
        response = table.delete_item(
            Key={'id': item_id},
            ConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={
                ':user_id': user_id
            },
            ReturnValues="ALL_OLD"
        )
        
        if 'Attributes' not in response:
            return build_response(404, {'message': 'Item not found'})
            
        return build_response(200, {'message': 'Item deleted successfully'})
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return build_response(403, {'message': 'Forbidden'})
        logger.error(f"DynamoDB error: {str(e)}")
        return build_response(500, {'message': 'Error deleting item'})
    except Exception as e:
        logger.error(f"Error deleting item: {str(e)}")
        return build_response(500, {'message': 'Internal server error'})
