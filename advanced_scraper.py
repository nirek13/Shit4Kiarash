#!/usr/bin/env python3
"""
Simple URL-based Scraper for condos.ca
Easy to use, focused on getting the job done
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import re
from typing import Dict, List, Any
from datetime import datetime


class SimpleCondosScraper:
    """
    Simple scraper for condos.ca - just pass URLs and get data!
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape a listing URL and return all the data
        
        Args:
            url: The condos.ca listing URL
            
        Returns:
            Dictionary with all the listing data
        """
        try:
            # Get the page
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract everything
            data = {
                'url': url,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                
                # Basic Info
                'address': self._get_text(soup, 'h1'),
                'price': self._get_text(soup, 'div', class_pattern='Price|AskingPrice'),
                'status': 'Sold' if soup.find('main', id=re.compile('Archived|Sold')) else 'Active',
                'days_on_market': self._get_text(soup, 'div', class_pattern='ListedDays'),
                
                # Property Details
                'bedrooms': self._extract_detail(soup, 'BD|Bed'),
                'bathrooms': self._extract_detail(soup, 'BA|Bath'),
                'parking': self._extract_detail(soup, 'Park'),
                'size': self._get_text(soup, 'div', class_pattern='Size|SqFt'),
                'floor': self._get_text(soup, 'span', class_pattern='Floor'),
                
                # Building & Location
                'building_name': self._get_text(soup, 'a', class_pattern='BuildingLink'),
                'neighborhood': self._get_first_location(soup),
                'city': self._get_city(soup),
                
                # Fees & Costs
                'maintenance_fee': self._get_text(soup, 'div', class_pattern='Maint'),
                'property_tax': self._get_text(soup, 'div', class_pattern='Tax'),
                
                # Agent Info
                'mls_number': self._get_text(soup, 'div', class_pattern='MLS|Mls'),
                'brokerage': self._get_text(soup, 'div', class_pattern='Brokerage'),
                
                # Images
                'images': self._get_images(soup),
                
                # Description
                'description': self._get_text(soup, 'div', class_pattern='Description|Details', 
                                           full=True)
            }
            
            # Clean up numeric values
            data['price_numeric'] = self._extract_number(data['price'])
            data['maintenance_fee_numeric'] = self._extract_number(data['maintenance_fee'])
            data['size_numeric'] = self._extract_number(data['size'])
            
            return data
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return {'url': url, 'error': str(e)}
    
    def scrape_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of condos.ca URLs
            
        Returns:
            List of scraped data dictionaries
        """
        results = []
        total = len(urls)
        
        for i, url in enumerate(urls, 1):
            print(f"Scraping {i}/{total}: {url}")
            result = self.scrape(url)
            results.append(result)
            time.sleep(1)  # Be nice to the server
        
        return results
    
    def save_json(self, data: Any, filename: str = 'listings.json'):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved to {filename}")
    
    def save_csv(self, data: List[Dict], filename: str = 'listings.csv'):
        """Save data to CSV file"""
        if not data:
            return
        
        # Prepare rows for CSV
        rows = []
        for item in data:
            if 'error' in item:
                continue
            row = {
                'URL': item.get('url', ''),
                'Address': item.get('address', ''),
                'Price': item.get('price', ''),
                'Price Numeric': item.get('price_numeric', ''),
                'Status': item.get('status', ''),
                'Days on Market': item.get('days_on_market', ''),
                'Bedrooms': item.get('bedrooms', ''),
                'Bathrooms': item.get('bathrooms', ''),
                'Parking': item.get('parking', ''),
                'Size': item.get('size', ''),
                'Size Numeric': item.get('size_numeric', ''),
                'Floor': item.get('floor', ''),
                'Building': item.get('building_name', ''),
                'Neighborhood': item.get('neighborhood', ''),
                'City': item.get('city', ''),
                'Maintenance Fee': item.get('maintenance_fee', ''),
                'MLS Number': item.get('mls_number', ''),
                'Brokerage': item.get('brokerage', ''),
                'Images Count': len(item.get('images', [])),
                'Scraped At': item.get('scraped_at', '')
            }
            rows.append(row)
        
        # Write CSV
        if rows:
            keys = rows[0].keys()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(rows)
            print(f"Saved {len(rows)} listings to {filename}")
    
    # Helper methods
    def _get_text(self, soup, tag, class_pattern=None, full=False):
        """Extract text from element"""
        if class_pattern:
            elem = soup.find(tag, class_=re.compile(class_pattern))
        else:
            elem = soup.find(tag)
        
        if elem:
            if full:
                return ' '.join(elem.stripped_strings)
            return elem.get_text(strip=True)
        return ''
    
    def _extract_detail(self, soup, pattern):
        """Extract property details like bedrooms, bathrooms"""
        items = soup.find_all('div', class_=re.compile('InfoItem|Spec'))
        for item in items:
            text = item.get_text(strip=True)
            if re.search(pattern, text, re.I):
                return text
        return ''
    
    def _get_first_location(self, soup):
        """Get the first location/neighborhood"""
        links = soup.find_all('a', class_=re.compile('AddressInlineLink|Location'))
        if links and len(links) > 0:
            return links[0].get_text(strip=True)
        return ''
    
    def _get_city(self, soup):
        """Get the city name"""
        links = soup.find_all('a', class_=re.compile('AddressInlineLink|Location'))
        for link in links:
            text = link.get_text(strip=True)
            if text.lower() in ['toronto', 'mississauga', 'brampton', 'vaughan', 'markham']:
                return text
        return ''
    
    def _get_images(self, soup):
        """Extract all image URLs"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and 'repliers' in src:
                # Get high-res version
                src = re.sub(r'width=\d+', 'width=1920', src)
                if src not in images:
                    images.append(src)
        return images
    
    def _extract_number(self, text):
        """Extract numeric value from text"""
        if not text:
            return None
        match = re.search(r'[\d,]+', text)
        if match:
            return int(match.group().replace(',', ''))
        return None


# Easy-to-use functions
def scrape_listing(url: str) -> Dict:
    """
    Scrape a single listing
    
    Example:
        data = scrape_listing("https://condos.ca/...")
        print(data['price'])
    """
    scraper = SimpleCondosScraper()
    return scraper.scrape(url)


def scrape_listings(urls: List[str], save_as: str = None) -> List[Dict]:
    """
    Scrape multiple listings
    
    Args:
        urls: List of URLs to scrape
        save_as: Optional filename to save results ('json' or 'csv' extension)
    
    Example:
        urls = ["url1", "url2", "url3"]
        data = scrape_listings(urls, save_as="results.csv")
    """
    scraper = SimpleCondosScraper()
    results = scraper.scrape_multiple(urls)
    
    if save_as:
        if save_as.endswith('.csv'):
            scraper.save_csv(results, save_as)
        else:
            scraper.save_json(results, save_as)
    
    return results


# Quick start example
if __name__ == "__main__":
    print("="*60)
    print("SIMPLE CONDOS.CA SCRAPER")
    print("="*60)
    
    # Example 1: Scrape one listing
    print("\n1. Scraping a single listing:")
    print("-"*40)
    
    url = "https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-703-C12469683"
    data = scrape_listing(url)
    
    # Print key information
    print(f"Address: {data.get('address', 'N/A')}")
    print(f"Price: {data.get('price', 'N/A')}")
    print(f"Bedrooms: {data.get('bedrooms', 'N/A')}")
    print(f"Bathrooms: {data.get('bathrooms', 'N/A')}")
    print(f"Size: {data.get('size', 'N/A')}")
    print(f"Building: {data.get('building_name', 'N/A')}")
    print(f"Status: {data.get('status', 'N/A')}")
    print(f"Images found: {len(data.get('images', []))}")
    
    # Save the data
    with open('single_listing_demo.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("\n✓ Full data saved to single_listing_demo.json")
    
    # Example 2: Scrape multiple listings (uncomment to use)
    """
    print("\n2. Scraping multiple listings:")
    print("-"*40)
    
    urls = [
        "https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-703-C12469683",
        "https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-511-C12469811",
        "https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-810-C12469805",
    ]
    
    # Scrape and save as CSV
    results = scrape_listings(urls, save_as="multiple_listings.csv")
    
    # Also save as JSON
    with open('multiple_listings.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Scraped {len(results)} listings")
    print("✓ Data saved to multiple_listings.csv and multiple_listings.json")
    """
    
    print("\n" + "="*60)
    print("Done! Check the usage examples in the code.")
    print("="*60)