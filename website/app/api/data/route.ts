// app/api/data/route.js

import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    // Define the path to the data.json file in the public directory
    const dataFilePath = path.join(process.cwd(), 'public', 'data.json');
    
    console.log(`Attempting to read data from: ${dataFilePath}`);
    
    // Check if the file exists
    if (!fs.existsSync(dataFilePath)) {
      console.error(`Data file not found at: ${dataFilePath}`);
      return new Response(JSON.stringify({ 
        error: 'Data file not found',
        message: `File not found at ${dataFilePath}`,
        checkedPath: dataFilePath
      }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json'
        }
      });
    }
    
    // Read the file
    const fileData = fs.readFileSync(dataFilePath, 'utf8');
    
    // Parse the JSON data
    const data = JSON.parse(fileData);
    console.log(`Successfully loaded data from ${dataFilePath}`);
    
    // Return the data with appropriate headers
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=3600' // Cache for 1 hour
      }
    });
  } catch (error) {
    console.error('Error reading ransomware data:', error);
    
    // Return error response with detailed information
    return new Response(JSON.stringify({ 
      error: 'Failed to load data',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
}