const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');
const readFile = promisify(fs.readFile);

// Configure AWS
AWS.config.update({ region: 'us-east-1' }); // Change to your preferred region
const cloudFormation = new AWS.CloudFormation();
const iam = new AWS.IAM();
const lambda = new AWS.Lambda();
const apiGateway = new AWS.APIGateway();
const dynamoDB = new AWS.DynamoDB();

// Stack configuration
const STACK_NAME = 'BasicBackendStack';
const STACK_TEMPLATE = 'template.yaml';
const LAMBDA_ZIP = 'function.zip';

async function deploy() {
  try {
    console.log('Deploying AWS Backend...');
    
    // 1. Create or update CloudFormation stack
    const templateBody = await readFile(path.join(__dirname, STACK_TEMPLATE), 'utf8');
    
    const stackExists = await checkStackExists(STACK_NAME);
    
    if (stackExists) {
      console.log('Updating existing stack...');
      await updateStack(templateBody);
    } else {
      console.log('Creating new stack...');
      await createStack(templateBody);
    }
    
    console.log('Deployment completed successfully!');
    
  } catch (error) {
    console.error('Deployment failed:', error);
    process.exit(1);
  }
}

async function checkStackExists(stackName) {
  try {
    await cloudFormation.describeStacks({ StackName: stackName }).promise();
    return true;
  } catch (error) {
    if (error.code === 'ValidationError' && error.message.includes('does not exist')) {
      return false;
    }
    throw error;
  }
}

async function createStack(templateBody) {
  const params = {
    StackName: STACK_NAME,
    TemplateBody: templateBody,
    Capabilities: ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
    OnFailure: 'ROLLBACK',
    TimeoutInMinutes: 30
  };
  
  await cloudFormation.createStack(params).promise();
  await cloudFormation.waitFor('stackCreateComplete', { StackName: STACK_NAME }).promise();
}

async function updateStack(templateBody) {
  const params = {
    StackName: STACK_NAME,
    TemplateBody: templateBody,
    Capabilities: ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
  };
  
  try {
    await cloudFormation.updateStack(params).promise();
    await cloudFormation.waitFor('stackUpdateComplete', { StackName: STACK_NAME }).promise();
  } catch (error) {
    if (error.message.includes('No updates are to be performed')) {
      console.log('No updates to perform');
      return;
    }
    throw error;
  }
}

// Start deployment
deploy();
