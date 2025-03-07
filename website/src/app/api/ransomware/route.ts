import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Type definitions
export interface Entity {
  id: string;
  domain: string;
  status: string;
  description_preview?: string;
  updated?: string;
  views?: number;
  countdown_remaining?: {
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
  };
  estimated_publish_date?: string;
  first_seen?: string;
  class?: string;
}

export interface RansomwareData {
  entities: Entity[];
  last_updated: string;
  total_count: number;
}

// Get the data directory path (one level up from website directory)
function getDataDirectoryPath(): string {
  return path.resolve(process.cwd(), '../data');
}

// Get the output directory path
function getOutputDirectoryPath(): string {
  return path.resolve(getDataDirectoryPath(), 'output');
}

// List all available ransomware files
function listRansomwareFiles(): string[] {
  const outputDir = getOutputDirectoryPath();
  
  try {
    if (!fs.existsSync(outputDir)) {
      console.error(`Output directory doesn't exist: ${outputDir}`);
      return [];
    }
    
    return fs.readdirSync(outputDir)
      .filter(file => file.endsWith('_entities.json'));
  } catch (error) {
    console.error('Error listing ransomware files:', error);
    return [];
  }
}

// Load ransomware data from a file
function loadRansomwareData(filename: string): RansomwareData | null {
  const filePath = path.join(getOutputDirectoryPath(), filename);
  
  try {
    if (!fs.existsSync(filePath)) {
      console.error(`File doesn't exist: ${filePath}`);
      return null;
    }
    
    const rawData = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(rawData) as RansomwareData;
  } catch (error) {
    console.error(`Error loading ransomware data from ${filename}:`, error);
    return null;
  }
}

// Get the latest target for a ransomware group
function getLatestTarget(data: RansomwareData): Entity | null {
  if (!data || !data.entities || data.entities.length === 0) {
    return null;
  }
  
  // Try to find the most recently updated entity
  const sortedEntities = [...data.entities].sort((a, b) => {
    if (!a.updated && !b.updated) return 0;
    if (!a.updated) return 1;
    if (!b.updated) return -1;
    
    return new Date(b.updated).getTime() - new Date(a.updated).getTime();
  });
  
  return sortedEntities[0];
}

// API handler
export async function GET() {
  try {
    const files = listRansomwareFiles();
    const sites = [];
    
    for (const file of files) {
      const data = loadRansomwareData(file);
      if (!data) continue;
      
      const key = file.replace('_entities.json', '');
      const name = key.charAt(0).toUpperCase() + key.slice(1); // Capitalize the name
      
      sites.push({
        key,
        name,
        data,
        latestTarget: getLatestTarget(data)
      });
    }
    
    return NextResponse.json(sites);
  } catch (error) {
    console.error('Error in API route:', error);
    return NextResponse.json(
      { error: 'Failed to load ransomware data' },
      { status: 500 }
    );
  }
}
