const express = require('express');
const AWS = require('aws-sdk');
const serverless = require('serverless-http');
const { v4: uuidv4 } = require('uuid');

// Initialize Express app
const app = express();
app.use(express.json());

// Configure AWS
const dynamoDb = new AWS.DynamoDB.DocumentClient();
const TABLE_NAME = process.env.TABLE_NAME || 'ItemsTable';

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Create item
app.post('/items', async (req, res) => {
  try {
    const id = uuidv4();
    const { name, description } = req.body;
    
    const params = {
      TableName: TABLE_NAME,
      Item: {
        id,
        name,
        description,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
    };

    await dynamoDb.put(params).promise();
    res.status(201).json(params.Item);
  } catch (error) {
    console.error('Error creating item:', error);
    res.status(500).json({ error: 'Could not create item' });
  }
});

// Get all items
app.get('/items', async (req, res) => {
  try {
    const params = {
      TableName: TABLE_NAME
    };

    const result = await dynamoDb.scan(params).promise();
    res.json(result.Items || []);
  } catch (error) {
    console.error('Error fetching items:', error);
    res.status(500).json({ error: 'Could not fetch items' });
  }
});

// Get single item
app.get('/items/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const params = {
      TableName: TABLE_NAME,
      Key: { id }
    };

    const result = await dynamoDb.get(params).promise();
    
    if (!result.Item) {
      return res.status(404).json({ error: 'Item not found' });
    }
    
    res.json(result.Item);
  } catch (error) {
    console.error('Error fetching item:', error);
    res.status(500).json({ error: 'Could not fetch item' });
  }
});

// Update item
app.put('/items/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { name, description } = req.body;
    
    const params = {
      TableName: TABLE_NAME,
      Key: { id },
      UpdateExpression: 'set #name = :name, description = :desc, updatedAt = :updatedAt',
      ExpressionAttributeNames: {
        '#name': 'name'
      },
      ExpressionAttributeValues: {
        ':name': name,
        ':desc': description,
        ':updatedAt': new Date().toISOString()
      },
      ReturnValues: 'ALL_NEW'
    };

    const result = await dynamoDb.update(params).promise();
    res.json(result.Attributes);
  } catch (error) {
    console.error('Error updating item:', error);
    res.status(500).json({ error: 'Could not update item' });
  }
});

// Delete item
app.delete('/items/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const params = {
      TableName: TABLE_NAME,
      Key: { id },
      ReturnValues: 'ALL_OLD'
    };

    const result = await dynamoDb.delete(params).promise();
    
    if (!result.Attributes) {
      return res.status(404).json({ error: 'Item not found' });
    }
    
    res.json({ message: 'Item deleted successfully' });
  } catch (error) {
    console.error('Error deleting item:', error);
    res.status(500).json({ error: 'Could not delete item' });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// Export the serverless handler
module.exports.handler = serverless(app);

// For local development
if (process.env.NODE_ENV !== 'production') {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
  });
}
