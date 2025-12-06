const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { spawn } = require('child_process');
const fs = require('fs-extra');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middlewar
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Utility function to run Python scripts
const runPythonScript = (scriptName, args = [], input = null) => {
  return new Promise((resolve, reject) => {
    const python = spawn('python3', [scriptName, ...args]);
    
    let stdout = '';
    let stderr = '';
    
    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    if (input) {
      python.stdin.write(JSON.stringify(input));
      python.stdin.end();
    }
    
    python.on('close', (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(stderr || `Process exited with code ${code}`));
      }
    });
    
    python.on('error', (error) => {
      reject(error);
    });
  });
};

// Root route - API documentation
app.get('/', (req, res) => {
  res.json({
    message: 'Real Estate Scraper REST API',
    version: '1.0.0',
    endpoints: {
      '/api/scraper': {
        'POST /api/scraper/advanced': 'Scrape using advanced scraper (body: {url: string})',
        'POST /api/scraper/advanced/multiple': 'Scrape multiple URLs (body: {urls: string[]})',
        'POST /api/scraper/comprehensive': 'Scrape using comprehensive scraper (body: {url: string})',
        'POST /api/scraper/comprehensive/multiple': 'Scrape multiple URLs comprehensively (body: {urls: string[]})'
      },
      '/health': 'Health check endpoint'
    }
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});
app.get('/test-python', (req, res) => {
  const { spawn } = require('child_process');
  const python = spawn('python3', ['--version']);

  let output = '';
  let error = '';

  python.stdout.on('data', (data) => { output += data.toString(); });
  python.stderr.on('data', (data) => { error += data.toString(); });

  python.on('close', (code) => {
    if (code === 0) {
      res.send({ success: true, python_version: output.trim() });
    } else {
      res.send({ success: false, error: error || `Exited with code ${code}` });
    }
  });

  python.on('error', (err) => {
    res.send({ success: false, error: err.message });
  });
});

// ============ SCRAPER ROUTES ============

// Advanced scraper - single URL
app.post('/api/scraper/advanced', async (req, res) => {
  try {
    const { url } = req.body;
    
    if (!url) {
      return res.status(400).json({
        success: false,
        error: 'URL is required'
      });
    }
    
    // Validate URL
    try {
      new URL(url);
    } catch {
      return res.status(400).json({
        success: false,
        error: 'Invalid URL format'
      });
    }
    
    const script = `
import sys
import json
sys.path.append('.')
from advanced_scraper import scrape_listing

url = "${url}"
result = scrape_listing(url)
print(json.dumps(result))
`;
    
    await fs.writeFile('temp_advanced_scrape.py', script);
    const output = await runPythonScript('temp_advanced_scrape.py');
    const result = JSON.parse(output.trim());
    await fs.remove('temp_advanced_scrape.py');
    
    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Advanced scraper - multiple URLs
app.post('/api/scraper/advanced/multiple', async (req, res) => {
  try {
    const { urls } = req.body;
    
    if (!urls || !Array.isArray(urls) || urls.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'URLs array is required'
      });
    }
    
    // Validate URLs
    for (const url of urls) {
      try {
        new URL(url);
      } catch {
        return res.status(400).json({
          success: false,
          error: `Invalid URL format: ${url}`
        });
      }
    }
    
    const script = `
import sys
import json
import io
from contextlib import redirect_stdout, redirect_stderr
sys.path.append('.')
from advanced_scraper import SimpleCondosScraper

# Create scraper and scrape URLs without progress messages
scraper = SimpleCondosScraper()
urls = ${JSON.stringify(urls)}
results = []

for url in urls:
    # Capture stdout to suppress progress messages
    f = io.StringIO()
    with redirect_stdout(f):
        result = scraper.scrape(url)
    results.append(result)

print(json.dumps(results))
`;
    
    await fs.writeFile('temp_advanced_multiple.py', script);
    const output = await runPythonScript('temp_advanced_multiple.py');
    const results = JSON.parse(output.trim());
    await fs.remove('temp_advanced_multiple.py');
    
    res.json({
      success: true,
      data: results,
      count: results.length
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Comprehensive scraper - single URL
app.post('/api/scraper/comprehensive', async (req, res) => {
  try {
    const { url } = req.body;
    
    if (!url) {
      return res.status(400).json({
        success: false,
        error: 'URL is required'
      });
    }
    
    // Validate URL
    try {
      new URL(url);
    } catch {
      return res.status(400).json({
        success: false,
        error: 'Invalid URL format'
      });
    }
    
    const script = `
import sys
import json
sys.path.append('.')
from real_estate_scraper import CondosURLScraper

scraper = CondosURLScraper(delay=0.5, verbose=False)
result = scraper.scrape_listing("${url}")
print(json.dumps(result))
`;
    
    await fs.writeFile('temp_comprehensive_scrape.py', script);
    const output = await runPythonScript('temp_comprehensive_scrape.py');
    const result = JSON.parse(output.trim());
    await fs.remove('temp_comprehensive_scrape.py');
    
    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Comprehensive scraper - multiple URLs
app.post('/api/scraper/comprehensive/multiple', async (req, res) => {
  try {
    const { urls } = req.body;
    
    if (!urls || !Array.isArray(urls) || urls.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'URLs array is required'
      });
    }
    
    // Validate URLs
    for (const url of urls) {
      try {
        new URL(url);
      } catch {
        return res.status(400).json({
          success: false,
          error: `Invalid URL format: ${url}`
        });
      }
    }
    
    const script = `
import sys
import json
import io
from contextlib import redirect_stdout, redirect_stderr
sys.path.append('.')
from real_estate_scraper import CondosURLScraper

scraper = CondosURLScraper(delay=0.5, verbose=False)
urls = ${JSON.stringify(urls)}

# Suppress any remaining print statements
f = io.StringIO()
with redirect_stdout(f):
    results = scraper.scrape_multiple(urls, save_progress=False)

print(json.dumps(results))
`;
    
    await fs.writeFile('temp_comprehensive_multiple.py', script);
    const output = await runPythonScript('temp_comprehensive_multiple.py');
    const results = JSON.parse(output.trim());
    await fs.remove('temp_comprehensive_multiple.py');
    
    res.json({
      success: true,
      data: results,
      count: results.length
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    success: false,
    error: 'Internal server error'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

// Start server
app.listen(PORT, () => {
  console.log(``);
  console.log(`🚀 Real Estate Scraper REST API`);
  console.log(`📍 Running on: http://localhost:${PORT}`);
  console.log(`📖 API Documentation: http://localhost:${PORT}`);
  console.log(``);
  console.log(`Available endpoints:`);
  console.log(`  GET  /                               - API documentation`);
  console.log(`  GET  /health                         - Health check`);
  console.log(`  POST /api/scraper/advanced           - Advanced scraping`);
  console.log(`  POST /api/scraper/advanced/multiple  - Multiple advanced scraping`);
  console.log(`  POST /api/scraper/comprehensive      - Comprehensive scraping`);
  console.log(`  POST /api/scraper/comprehensive/multiple - Multiple comprehensive scraping`);
  console.log(``);
});
