const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { spawn } = require('child_process');
const fs = require('fs-extra');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
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
    message: 'Python Scripts REST API',
    version: '1.0.0',
    endpoints: {
      '/api/payout': {
        'GET /api/payout/calculate/:views': 'Calculate payout for given view count',
        'POST /api/payout/calculate': 'Calculate payout (body: {views: number})',
        'GET /api/payout/benchmarks': 'Get all benchmark data points',
        'GET /api/payout/chart-data': 'Get data for plotting payout chart'
      },
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

// ============ PAYOUT ROUTES ============

// Get benchmark data
app.get('/api/payout/benchmarks', async (req, res) => {
  try {
    const script = `
import math

benchmarks = [
    (10000, 45),
    (25000, 80),
    (50000, 160),
    (100000, 260),
    (250000, 370),
    (500000, 650),
    (1000000, 850),
    (5000000, 2500),
]

print(f'{benchmarks}')
`;
    
    await fs.writeFile('temp_benchmarks.py', script);
    const output = await runPythonScript('temp_benchmarks.py');
    const benchmarks = eval(output.trim());
    await fs.remove('temp_benchmarks.py');
    
    res.json({
      success: true,
      data: benchmarks.map(([views, payout]) => ({ views, payout }))
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Calculate payout for specific views (GET)
app.get('/api/payout/calculate/:views', async (req, res) => {
  try {
    const views = parseInt(req.params.views);
    
    if (isNaN(views) || views <= 0) {
      return res.status(400).json({
        success: false,
        error: 'Views must be a positive number'
      });
    }
    
    const script = `
import math

benchmarks = [
    (10000, 45),
    (25000, 80),
    (50000, 160),
    (100000, 260),
    (250000, 370),
    (500000, 650),
    (1000000, 850),
    (5000000, 2500),
]

def payout(views: int) -> int:
    if views <= benchmarks[0][0]:
        return benchmarks[0][1]
    if views >= benchmarks[-1][0]:
        return benchmarks[-1][1]

    for i in range(len(benchmarks)-1):
        v0, p0 = benchmarks[i]
        v1, p1 = benchmarks[i+1]
        if v0 <= views <= v1:
            log_ratio = (math.log10(views) - math.log10(v0)) / (math.log10(v1) - math.log10(v0))
            payout_value = p0 + log_ratio * (p1 - p0)
            return round(payout_value)

views = ${views}
result = payout(views)
print(f'{{"views": {views}, "payout": {result}}}')
`;
    
    await fs.writeFile('temp_payout.py', script);
    const output = await runPythonScript('temp_payout.py');
    const result = JSON.parse(output.trim());
    await fs.remove('temp_payout.py');
    
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

// Calculate payout for specific views (POST)
app.post('/api/payout/calculate', async (req, res) => {
  try {
    const { views } = req.body;
    
    if (!views || isNaN(views) || views <= 0) {
      return res.status(400).json({
        success: false,
        error: 'Views must be a positive number'
      });
    }
    
    const script = `
import math

benchmarks = [
    (10000, 45),
    (25000, 80),
    (50000, 160),
    (100000, 260),
    (250000, 370),
    (500000, 650),
    (1000000, 850),
    (5000000, 2500),
]

def payout(views: int) -> int:
    if views <= benchmarks[0][0]:
        return benchmarks[0][1]
    if views >= benchmarks[-1][0]:
        return benchmarks[-1][1]

    for i in range(len(benchmarks)-1):
        v0, p0 = benchmarks[i]
        v1, p1 = benchmarks[i+1]
        if v0 <= views <= v1:
            log_ratio = (math.log10(views) - math.log10(v0)) / (math.log10(v1) - math.log10(v0))
            payout_value = p0 + log_ratio * (p1 - p0)
            return round(payout_value)

views = ${parseInt(views)}
result = payout(views)
print(f'{{"views": {views}, "payout": {result}}}')
`;
    
    await fs.writeFile('temp_payout.py', script);
    const output = await runPythonScript('temp_payout.py');
    const result = JSON.parse(output.trim());
    await fs.remove('temp_payout.py');
    
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

// Get chart data for plotting
app.get('/api/payout/chart-data', async (req, res) => {
  try {
    const { start = 1000, end = 5000000, step = 10000 } = req.query;
    
    const script = `
import math

benchmarks = [
    (10000, 45),
    (25000, 80),
    (50000, 160),
    (100000, 260),
    (250000, 370),
    (500000, 650),
    (1000000, 850),
    (5000000, 2500),
]

def payout(views: int) -> int:
    if views <= benchmarks[0][0]:
        return benchmarks[0][1]
    if views >= benchmarks[-1][0]:
        return benchmarks[-1][1]

    for i in range(len(benchmarks)-1):
        v0, p0 = benchmarks[i]
        v1, p1 = benchmarks[i+1]
        if v0 <= views <= v1:
            log_ratio = (math.log10(views) - math.log10(v0)) / (math.log10(v1) - math.log10(v0))
            payout_value = p0 + log_ratio * (p1 - p0)
            return round(payout_value)

import json

start = ${parseInt(start)}
end = ${parseInt(end)}
step = ${parseInt(step)}

chart_data = []
for views in range(start, end + 1, step):
    chart_data.append({"views": views, "payout": payout(views)})

print(json.dumps({"chart_data": chart_data, "benchmarks": [{"views": v, "payout": p} for v, p in benchmarks]}))
`;
    
    await fs.writeFile('temp_chart.py', script);
    const output = await runPythonScript('temp_chart.py');
    const result = JSON.parse(output.trim());
    await fs.remove('temp_chart.py');
    
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
sys.path.append('.')
from advanced_scraper import scrape_listings

urls = ${JSON.stringify(urls)}
results = scrape_listings(urls)
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
sys.path.append('.')
from real_estate_scraper import CondosURLScraper

scraper = CondosURLScraper(delay=0.5, verbose=False)
urls = ${JSON.stringify(urls)}
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
  console.log(\`\`);
  console.log(\`🚀 Python Scripts REST API Server\`);
  console.log(\`📍 Running on: http://localhost:\${PORT}\`);
  console.log(\`📖 API Documentation: http://localhost:\${PORT}\`);
  console.log(\`\`);
  console.log(\`Available endpoints:\`);
  console.log(\`  GET  /                               - API documentation\`);
  console.log(\`  GET  /health                         - Health check\`);
  console.log(\`  GET  /api/payout/benchmarks          - Get payout benchmarks\`);
  console.log(\`  GET  /api/payout/calculate/:views    - Calculate payout for views\`);
  console.log(\`  POST /api/payout/calculate           - Calculate payout\`);
  console.log(\`  GET  /api/payout/chart-data          - Get chart data\`);
  console.log(\`  POST /api/scraper/advanced           - Advanced scraping\`);
  console.log(\`  POST /api/scraper/advanced/multiple  - Multiple advanced scraping\`);
  console.log(\`  POST /api/scraper/comprehensive      - Comprehensive scraping\`);
  console.log(\`  POST /api/scraper/comprehensive/multiple - Multiple comprehensive scraping\`);
  console.log(\`\`);
});