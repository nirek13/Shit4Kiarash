# Real Estate Scraper REST API

A Node.js REST API server that provides HTTP endpoints for Python real estate scraping scripts, specifically for condos.ca property listings.

## 🚀 Quick Start

### Prerequisites
- Node.js (v14 or higher)
- Python 3.x
- npm or yarn

### Installation

1. **Install Node.js dependencies:**
```bash
npm install
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Start the server:**
```bash
npm start
```

The API will be available at `http://localhost:3000`

## 📚 API Documentation

Visit `http://localhost:3000` for interactive API documentation.

## 🛠️ Available Scripts

This API provides endpoints for the following Python scripts:

### 1. Advanced Real Estate Scraper (`advanced_scraper.py`)
Simplified scraper for condos.ca listings with quick data extraction.

### 2. Comprehensive Real Estate Scraper (`real_estate_scraper.py`)
Full-featured scraper for condos.ca with comprehensive data extraction including property details, pricing, building info, location data, and more.

## 🔗 API Endpoints

### Real Estate Scraper Endpoints

#### Advanced Scraper - Single URL
```http
POST /api/scraper/advanced
Content-Type: application/json

{
  "url": "https://condos.ca/..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "url": "https://condos.ca/...",
    "address": "123 Main St",
    "price": "$500,000",
    "bedrooms": "2 BD",
    "bathrooms": "2 BA",
    "size": "750 sqft",
    // ... more property data
  }
}
```

#### Advanced Scraper - Multiple URLs
```http
POST /api/scraper/advanced/multiple
Content-Type: application/json

{
  "urls": [
    "https://condos.ca/listing1",
    "https://condos.ca/listing2"
  ]
}
```

#### Comprehensive Scraper - Single URL
```http
POST /api/scraper/comprehensive
Content-Type: application/json

{
  "url": "https://condos.ca/..."
}
```

Returns detailed property information including:
- Property specifications (bedrooms, bathrooms, parking)
- Pricing details (asking price, maintenance fees, taxes)
- Building information (name, year built, amenities)
- Location data (neighborhood, walk score, transit score)
- Agent information (MLS number, brokerage)
- Images and descriptions
- Nearby listings

#### Comprehensive Scraper - Multiple URLs
```http
POST /api/scraper/comprehensive/multiple
Content-Type: application/json

{
  "urls": [
    "https://condos.ca/listing1",
    "https://condos.ca/listing2"
  ]
}
```

### Utility Endpoints

#### Health Check
```http
GET /health
```

## 🧪 Testing the API

### Using cURL

**Test real estate scraping:**
```bash
curl -X POST http://localhost:3000/api/scraper/advanced \
  -H "Content-Type: application/json" \
  -d '{"url": "https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-703-C12469683"}'
```

### Using JavaScript/Fetch

```javascript
// Scrape real estate listing
const scrapeResponse = await fetch('http://localhost:3000/api/scraper/advanced', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ 
    url: 'https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-703-C12469683' 
  })
});
const scrapeData = await scrapeResponse.json();
console.log(scrapeData);
```

### Using Python requests

```python
import requests

# Scrape real estate listing
response = requests.post('http://localhost:3000/api/scraper/advanced',
                        json={'url': 'https://condos.ca/...'})
print(response.json())
```

## 📁 Project Structure

```
├── server.js              # Main Express server
├── package.json           # Node.js dependencies
├── requirements.txt       # Python dependencies
├── advanced_scraper.py   # Simple real estate scraper
├── real_estate_scraper.py # Comprehensive real estate scraper
├── venv/                 # Python virtual environment
└── README.md             # This file
```

## ⚙️ Configuration

### Environment Variables

- `PORT`: Server port (default: 3000)

### Python Dependencies

The API requires the following Python packages:
- `requests>=2.31.0`
- `beautifulsoup4>=4.12.0`
- `lxml>=4.9.0`

### Rate Limiting

The scraping endpoints include built-in rate limiting to be respectful to target websites. The comprehensive scraper includes a default 0.5-second delay between requests.

## 🚨 Important Notes

### Legal and Ethical Considerations

- **Respect robots.txt**: Always check the target website's robots.txt file before scraping
- **Rate limiting**: The scrapers include delays between requests to avoid overwhelming servers
- **Terms of Service**: Ensure your use complies with the website's Terms of Service
- **Personal use**: This tool is intended for educational and personal use only

### Error Handling

All endpoints return standardized error responses:

```json
{
  "success": false,
  "error": "Error message here"
}
```

Common error scenarios:
- Invalid URLs
- Network timeouts
- Missing required parameters
- Python script execution errors

## 🔧 Development

### Running in Development Mode

```bash
npm run dev
```

This uses nodemon for auto-reloading when files change.

### Adding New Endpoints

1. Add your Python script to the project directory
2. Create corresponding routes in `server.js`
3. Update this README with the new endpoint documentation

### Debugging

The server logs all Python script outputs and errors to the console. Check the terminal for detailed error information.

## 📈 Performance Considerations

- **Caching**: Consider implementing Redis caching for frequently requested data
- **Queue System**: For high-volume scraping, consider using a job queue (Bull.js, etc.)
- **Database**: Store scraped data in a database for persistence and faster retrieval
- **Rate Limiting**: Implement API rate limiting for production use

## 🔒 Security

For production deployment, consider:
- API authentication (JWT tokens, API keys)
- Input validation and sanitization
- CORS configuration
- HTTPS/SSL certificates
- Request rate limiting
- Input size limits

## 📞 Support

If you encounter any issues:
1. Check that all dependencies are installed correctly
2. Verify Python scripts work independently
3. Check the server logs for detailed error messages
4. Ensure target websites are accessible

## 🎯 Use Cases

This API is perfect for:
- **Real Estate Research**: Gather property data for market analysis
- **Data Pipeline Integration**: Include scraping capabilities in larger applications
- **Rapid Prototyping**: Quickly test ideas without setting up Python environments
- **Educational Projects**: Learn about web scraping and API development
- **Property Market Analysis**: Analyze trends and pricing in the GTA condo market

---

**Happy coding!** 🚀