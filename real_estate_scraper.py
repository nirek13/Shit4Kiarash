#!/usr/bin/env python3
"""
URL-based Real Estate Scraper for condos.ca
Scrapes property listings directly from URLs
"""

import re
import json
import time
import csv
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import requests
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
import os


class CondosURLScraper:
    """
    URL-based scraper for condos.ca real estate listings
    """
    
    def __init__(self, delay: float = 1.0, verbose: bool = True):
        """
        Initialize the scraper
        
        Args:
            delay: Delay between requests in seconds (be respectful to the server)
            verbose: Print progress messages
        """
        self.base_url = "https://condos.ca"
        self.delay = delay
        self.verbose = verbose
        self.session = requests.Session()
        
        # Set proper headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        self.scraped_count = 0
        self.failed_urls = []
    
    def scrape_listing(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single listing from its URL
        
        Args:
            url: Full URL of the listing
            
        Returns:
            Dictionary containing all scraped data
        """
        if self.verbose:
            print(f"Scraping: {url}")
        
        try:
            # Make request
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract all data
            listing_data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'status': 'success',
                'property': self._extract_property_info(soup),
                'pricing': self._extract_pricing(soup),
                'specifications': self._extract_specifications(soup),
                'building': self._extract_building_info(soup),
                'location': self._extract_location(soup),
                'features': self._extract_features(soup),
                'amenities': self._extract_amenities(soup),
                'description': self._extract_description(soup),
                'images': self._extract_images(soup),
                'agent': self._extract_agent_info(soup),
                'nearby_listings': self._extract_nearby_listings(soup)
            }
            
            self.scraped_count += 1
            
            # Respect rate limiting
            time.sleep(self.delay)
            
            return listing_data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed for {url}: {str(e)}"
            if self.verbose:
                print(f"ERROR: {error_msg}")
            self.failed_urls.append(url)
            return {
                'url': url,
                'status': 'error',
                'error': error_msg,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Parsing failed for {url}: {str(e)}"
            if self.verbose:
                print(f"ERROR: {error_msg}")
            self.failed_urls.append(url)
            return {
                'url': url,
                'status': 'error', 
                'error': error_msg,
                'scraped_at': datetime.now().isoformat()
            }
    
    def _extract_property_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract basic property information"""
        info = {}
        
        # Unit address/title
        title = soup.find('h1', class_=re.compile(r'Title|style___Title'))
        if title:
            info['unit_address'] = title.get_text(strip=True)
            # Parse unit number if present
            unit_match = re.match(r'^(\d+)\s*-\s*(.+)$', info['unit_address'])
            if unit_match:
                info['unit_number'] = unit_match.group(1)
                info['street_address'] = unit_match.group(2)
        
        # Property type (condo, townhouse, etc.)
        prop_type = soup.find('span', class_=re.compile(r'PropertyType|Type'))
        if prop_type:
            info['property_type'] = prop_type.get_text(strip=True)
        
        # Listing status
        status_elem = soup.find('span', class_=re.compile(r'Status|ListingStatus'))
        if status_elem:
            info['listing_status'] = status_elem.get_text(strip=True)
        elif soup.find('main', id=re.compile(r'Archived|Sold')):
            info['listing_status'] = 'Sold/Archived'
        else:
            info['listing_status'] = 'Active'
        
        # Days on market
        days_elem = soup.find('div', class_=re.compile(r'ListedDays|DaysOnMarket'))
        if days_elem:
            days_text = days_elem.get_text(strip=True)
            info['days_on_market'] = days_text
            # Extract numeric value
            days_num = re.search(r'(\d+)', days_text)
            if days_num:
                info['days_on_market_numeric'] = int(days_num.group(1))
        
        return info
    
    def _extract_pricing(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract pricing information"""
        pricing = {}
        
        # Asking price
        price_elem = soup.find('div', class_=re.compile(r'Price|AskingPrice'))
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            pricing['asking_price'] = price_text
            
            # Extract numeric value
            price_match = re.search(r'\$?([\d,]+)', price_text)
            if price_match:
                pricing['price_numeric'] = int(price_match.group(1).replace(',', ''))
        
        # Maintenance/Condo fees
        maint_elem = soup.find('div', class_=re.compile(r'Maint|MaintenanceFee'))
        if maint_elem:
            maint_text = maint_elem.get_text(strip=True)
            pricing['maintenance_fee'] = maint_text
            
            # Extract numeric value
            maint_match = re.search(r'\$?([\d,]+)', maint_text)
            if maint_match:
                pricing['maintenance_fee_numeric'] = int(maint_match.group(1).replace(',', ''))
        
        # Property taxes
        tax_elem = soup.find('div', class_=re.compile(r'Tax|PropertyTax'))
        if tax_elem:
            tax_text = tax_elem.get_text(strip=True)
            pricing['property_tax'] = tax_text
            
            # Extract numeric value
            tax_match = re.search(r'\$?([\d,]+)', tax_text)
            if tax_match:
                pricing['property_tax_numeric'] = int(tax_match.group(1).replace(',', ''))
        
        # Price per square foot
        ppsf_elem = soup.find('span', class_=re.compile(r'PricePerSqFt|PerSqFt'))
        if ppsf_elem:
            pricing['price_per_sqft'] = ppsf_elem.get_text(strip=True)
        
        return pricing
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract property specifications"""
        specs = {}
        
        # Bedrooms, Bathrooms, Parking
        info_items = soup.find_all('div', class_=re.compile(r'InfoItem|Spec|Feature'))
        for item in info_items:
            text = item.get_text(strip=True)
            
            # Bedrooms
            if 'BD' in text or 'Bed' in text.title():
                specs['bedrooms'] = text
                bed_match = re.search(r'(\d+\+?\d*)', text)
                if bed_match:
                    specs['bedrooms_numeric'] = bed_match.group(1)
            
            # Bathrooms
            elif 'BA' in text or 'Bath' in text.title():
                specs['bathrooms'] = text
                bath_match = re.search(r'(\d+)', text)
                if bath_match:
                    specs['bathrooms_numeric'] = int(bath_match.group(1))
            
            # Parking
            elif 'Park' in text.title():
                specs['parking'] = text
                park_match = re.search(r'(\d+)', text)
                if park_match:
                    specs['parking_spaces'] = int(park_match.group(1))
        
        # Square footage
        size_elem = soup.find('div', class_=re.compile(r'Size|SquareFeet|SqFt'))
        if size_elem:
            size_text = size_elem.get_text(strip=True)
            specs['size'] = size_text
            
            # Extract numeric range or value
            size_match = re.search(r'(\d+)[\s-]*(?:to|-)?\s*(\d+)?', size_text)
            if size_match:
                if size_match.group(2):
                    specs['size_min'] = int(size_match.group(1))
                    specs['size_max'] = int(size_match.group(2))
                else:
                    specs['size_sqft'] = int(size_match.group(1))
        
        # Floor level
        floor_elem = soup.find('span', class_=re.compile(r'Floor|Level'))
        if floor_elem:
            specs['floor'] = floor_elem.get_text(strip=True)
        
        # Exposure/View
        exposure_elem = soup.find('span', class_=re.compile(r'Exposure|View|Facing'))
        if exposure_elem:
            specs['exposure'] = exposure_elem.get_text(strip=True)
        
        return specs
    
    def _extract_building_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract building information"""
        building = {}
        
        # Building name and link
        building_link = soup.find('a', class_=re.compile(r'BuildingLink|BuildingName'))
        if building_link:
            building['name'] = building_link.get_text(strip=True)
            building['url'] = urljoin(self.base_url, building_link.get('href', ''))
        
        # Year built
        year_elem = soup.find('span', class_=re.compile(r'YearBuilt|Built'))
        if year_elem:
            year_text = year_elem.get_text(strip=True)
            year_match = re.search(r'(\d{4})', year_text)
            if year_match:
                building['year_built'] = int(year_match.group(1))
        
        # Total units in building
        units_elem = soup.find('span', class_=re.compile(r'TotalUnits|Units'))
        if units_elem:
            units_text = units_elem.get_text(strip=True)
            units_match = re.search(r'(\d+)', units_text)
            if units_match:
                building['total_units'] = int(units_match.group(1))
        
        # Number of floors
        floors_elem = soup.find('span', class_=re.compile(r'Floors|Stories|Storeys'))
        if floors_elem:
            floors_text = floors_elem.get_text(strip=True)
            floors_match = re.search(r'(\d+)', floors_text)
            if floors_match:
                building['total_floors'] = int(floors_match.group(1))
        
        return building
    
    def _extract_location(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract location information"""
        location = {}
        
        # Neighborhood hierarchy
        location_links = soup.find_all('a', class_=re.compile(r'AddressInlineLink|Location|Neighborhood'))
        if location_links:
            location['areas'] = []
            for link in location_links:
                area = {
                    'name': link.get_text(strip=True),
                    'url': urljoin(self.base_url, link.get('href', ''))
                }
                location['areas'].append(area)
            
            # Set specific location levels if identifiable
            if len(location['areas']) >= 1:
                location['neighborhood'] = location['areas'][0]['name']
            if len(location['areas']) >= 2:
                location['district'] = location['areas'][1]['name']
            if len(location['areas']) >= 3:
                location['city'] = location['areas'][2]['name']
        
        # Full address
        address_div = soup.find('div', class_=re.compile(r'Address|FullAddress'))
        if address_div:
            location['full_address'] = address_div.get_text(strip=True)
        
        # Walk Score, Transit Score
        scores = soup.find_all('div', class_=re.compile(r'Score'))
        for score in scores:
            score_text = score.get_text(strip=True)
            if 'Walk' in score_text:
                location['walk_score'] = score_text
                score_num = re.search(r'(\d+)', score_text)
                if score_num:
                    location['walk_score_numeric'] = int(score_num.group(1))
            elif 'Transit' in score_text:
                location['transit_score'] = score_text
                score_num = re.search(r'(\d+)', score_text)
                if score_num:
                    location['transit_score_numeric'] = int(score_num.group(1))
        
        return location
    
    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """Extract property features"""
        features = []
        
        # Look for feature lists
        feature_containers = soup.find_all(['ul', 'div'], class_=re.compile(r'Features?|Highlights?|Amenities'))
        
        for container in feature_containers:
            items = container.find_all(['li', 'span', 'div'])
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) < 100 and text not in features:
                    features.append(text)
        
        return features
    
    def _extract_amenities(self, soup: BeautifulSoup) -> List[str]:
        """Extract building amenities"""
        amenities = []
        
        amenity_section = soup.find('div', class_=re.compile(r'BuildingAmenities|Amenities'))
        if amenity_section:
            items = amenity_section.find_all(['li', 'span'])
            for item in items:
                text = item.get_text(strip=True)
                if text and text not in amenities:
                    amenities.append(text)
        
        return amenities
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract property description"""
        description = ""
        
        desc_elem = soup.find('div', class_=re.compile(r'Description|Details|About'))
        if desc_elem:
            # Get all paragraph text
            paragraphs = desc_elem.find_all(['p', 'div'])
            desc_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # Filter out short fragments
                    desc_parts.append(text)
            description = ' '.join(desc_parts)
        
        return description
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract image URLs"""
        images = []
        seen_urls = set()
        
        # Find all images
        img_elements = soup.find_all('img')
        for img in img_elements:
            src = img.get('src') or img.get('data-src')
            if src and 'repliers' in src and src not in seen_urls:
                # Get high-res version
                high_res = re.sub(r'width=\d+', 'width=1920', src)
                images.append({
                    'url': high_res,
                    'thumbnail': src,
                    'alt': img.get('alt', '')
                })
                seen_urls.add(src)
        
        # Look for gallery data
        gallery = soup.find('div', class_=re.compile(r'Gallery|ImageGallery'))
        if gallery:
            gallery_images = gallery.find_all(['a', 'div'], {'data-src': True})
            for elem in gallery_images:
                src = elem.get('data-src')
                if src and src not in seen_urls:
                    images.append({
                        'url': src,
                        'thumbnail': src,
                        'alt': ''
                    })
                    seen_urls.add(src)
        
        return images
    
    def _extract_agent_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract agent/brokerage information"""
        agent = {}
        
        # MLS number
        mls_elem = soup.find('div', class_=re.compile(r'MLS|Mls'))
        if mls_elem:
            mls_text = mls_elem.get_text(strip=True)
            agent['mls_number'] = mls_text
            # Extract just the number
            mls_match = re.search(r'([A-Z]?\d+)', mls_text)
            if mls_match:
                agent['mls_id'] = mls_match.group(1)
        
        # Brokerage
        brokerage_elem = soup.find('div', class_=re.compile(r'Brokerage|Broker'))
        if brokerage_elem:
            agent['brokerage'] = brokerage_elem.get_text(strip=True)
        
        # Agent name
        agent_elem = soup.find('div', class_=re.compile(r'Agent|Realtor|ListedBy'))
        if agent_elem:
            agent['agent_name'] = agent_elem.get_text(strip=True)
        
        # Contact info
        phone_elem = soup.find('a', href=re.compile(r'tel:'))
        if phone_elem:
            agent['phone'] = phone_elem.get_text(strip=True)
        
        email_elem = soup.find('a', href=re.compile(r'mailto:'))
        if email_elem:
            agent['email'] = email_elem.get_text(strip=True)
        
        return agent
    
    def _extract_nearby_listings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract nearby/similar listings"""
        listings = []
        
        # Find listing cards
        cards = soup.find_all('div', class_=re.compile(r'ListingPreview|PropertyCard'))[:10]
        
        for card in cards:
            listing = {}
            
            # Address
            addr_elem = card.find(['address', 'div'], class_=re.compile(r'Address'))
            if addr_elem:
                listing['address'] = addr_elem.get_text(strip=True)
            
            # Price
            price_elem = card.find('div', class_=re.compile(r'Price'))
            if price_elem:
                listing['price'] = price_elem.get_text(strip=True)
            
            # Specs
            specs_elem = card.find('div', class_=re.compile(r'InfoHolder|Specs'))
            if specs_elem:
                listing['specs'] = specs_elem.get_text(strip=True)
            
            # Link
            link_elem = card.find('a', href=True)
            if link_elem:
                listing['url'] = urljoin(self.base_url, link_elem.get('href'))
            
            if listing:
                listings.append(listing)
        
        return listings
    
    def scrape_multiple(self, urls: List[str], save_progress: bool = True) -> List[Dict[str, Any]]:
        """
        Scrape multiple listings from URLs
        
        Args:
            urls: List of listing URLs to scrape
            save_progress: Save progress after every 5 listings
            
        Returns:
            List of scraped data dictionaries
        """
        results = []
        total = len(urls)
        
        if self.verbose:
            print(f"Starting to scrape {total} listings...")
            print("="*50)
        
        for i, url in enumerate(urls, 1):
            if self.verbose:
                print(f"\n[{i}/{total}] ", end="")
            
            # Scrape the listing
            result = self.scrape_listing(url)
            results.append(result)
            
            # Save progress periodically
            if save_progress and i % 5 == 0:
                self._save_progress(results, f'progress_{i}_of_{total}.json')
            
            # Print summary
            if self.verbose and result['status'] == 'success':
                prop = result.get('property', {})
                price = result.get('pricing', {})
                print(f"✓ {prop.get('unit_address', 'Unknown')} - {price.get('asking_price', 'N/A')}")
        
        if self.verbose:
            print("\n" + "="*50)
            print(f"Scraping complete! Successfully scraped {self.scraped_count}/{total} listings")
            if self.failed_urls:
                print(f"Failed URLs ({len(self.failed_urls)}):")
                for url in self.failed_urls:
                    print(f"  - {url}")
        
        return results
    
    def _save_progress(self, data: List[Dict], filename: str):
        """Save scraping progress to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if self.verbose:
            print(f"\n  → Progress saved to {filename}")
    
    def save_to_json(self, data: Any, filename: str):
        """
        Save scraped data to JSON file
        
        Args:
            data: Data to save (single listing or list of listings)
            filename: Output filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if self.verbose:
            print(f"Data saved to {filename}")
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str):
        """
        Save scraped data to CSV file
        
        Args:
            data: List of listing dictionaries
            filename: Output CSV filename
        """
        if not data:
            return
        
        # Prepare flattened data for CSV
        csv_data = []
        
        for listing in data:
            if listing.get('status') != 'success':
                continue
                
            row = {
                'URL': listing.get('url', ''),
                'Scraped At': listing.get('scraped_at', ''),
                
                # Property info
                'Unit Address': listing.get('property', {}).get('unit_address', ''),
                'Unit Number': listing.get('property', {}).get('unit_number', ''),
                'Property Type': listing.get('property', {}).get('property_type', ''),
                'Status': listing.get('property', {}).get('listing_status', ''),
                'Days on Market': listing.get('property', {}).get('days_on_market_numeric', ''),
                
                # Pricing
                'Asking Price': listing.get('pricing', {}).get('asking_price', ''),
                'Price Numeric': listing.get('pricing', {}).get('price_numeric', ''),
                'Maintenance Fee': listing.get('pricing', {}).get('maintenance_fee', ''),
                'Property Tax': listing.get('pricing', {}).get('property_tax', ''),
                
                # Specifications
                'Bedrooms': listing.get('specifications', {}).get('bedrooms', ''),
                'Bathrooms': listing.get('specifications', {}).get('bathrooms', ''),
                'Parking': listing.get('specifications', {}).get('parking', ''),
                'Size': listing.get('specifications', {}).get('size', ''),
                'Floor': listing.get('specifications', {}).get('floor', ''),
                
                # Building
                'Building Name': listing.get('building', {}).get('name', ''),
                'Year Built': listing.get('building', {}).get('year_built', ''),
                
                # Location
                'Neighborhood': listing.get('location', {}).get('neighborhood', ''),
                'City': listing.get('location', {}).get('city', ''),
                'Walk Score': listing.get('location', {}).get('walk_score_numeric', ''),
                
                # Agent
                'MLS Number': listing.get('agent', {}).get('mls_id', ''),
                'Brokerage': listing.get('agent', {}).get('brokerage', ''),
                
                # Other
                'Features': ', '.join(listing.get('features', [])),
                'Amenities': ', '.join(listing.get('amenities', [])),
                'Image Count': len(listing.get('images', []))
            }
            
            csv_data.append(row)
        
        # Write to CSV
        if csv_data:
            keys = csv_data[0].keys()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(csv_data)
            
            if self.verbose:
                print(f"CSV data saved to {filename} ({len(csv_data)} listings)")


def main():
    """
    Example usage of the URL-based scraper
    """
    
    # Initialize scraper
    scraper = CondosURLScraper(delay=1.0, verbose=True)
    
    print("="*60)
    print("CONDOS.CA URL-BASED SCRAPER")
    print("="*60)
    
    # Example URLs (you can replace these with actual URLs)
    example_urls = [
        "https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-703-C12469683",
        # Add more URLs here as needed
    ]
    
    # Example 1: Scrape a single listing
    print("\nExample 1: Scraping a single listing")
    print("-"*40)
    
    url = "https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-703-C12469683"
    result = scraper.scrape_listing(url)
    
    # Save single listing
    scraper.save_to_json(result, 'single_listing.json')
    
    # Print summary
    if result['status'] == 'success':
        print(f"\nProperty: {result['property'].get('unit_address', 'N/A')}")
        print(f"Price: {result['pricing'].get('asking_price', 'N/A')}")
        print(f"Specs: {result['specifications'].get('bedrooms', 'N/A')} | {result['specifications'].get('bathrooms', 'N/A')}")
        print(f"Size: {result['specifications'].get('size', 'N/A')}")
        print(f"Building: {result['building'].get('name', 'N/A')}")
        print(f"Location: {result['location'].get('neighborhood', 'N/A')}")
    
    # Example 2: Scrape multiple listings (uncomment to use)
    """
    print("\nExample 2: Scraping multiple listings")
    print("-"*40)
    
    urls = [
        "https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-703-C12469683",
        "https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-511-C12469811",
        "https://condos.ca/toronto/westmount-boutique-residences-700-sheppard-ave-w-716-sheppard-ave-w/unit-810-C12469805",
        # Add more URLs
    ]
    
    results = scraper.scrape_multiple(urls)
    
    # Save results
    scraper.save_to_json(results, 'all_listings.json')
    scraper.save_to_csv(results, 'listings.csv')
    """
    
    # Example 3: Batch scraping with CSV input (uncomment to use)
    """
    print("\nExample 3: Batch scraping from CSV")
    print("-"*40)
    
    # Read URLs from CSV file
    import csv
    with open('urls.csv', 'r') as f:
        reader = csv.reader(f)
        urls = [row[0] for row in reader if row]
    
    results = scraper.scrape_multiple(urls)
    scraper.save_to_json(results, 'batch_results.json')
    scraper.save_to_csv(results, 'batch_results.csv')
    """
    
    print("\n" + "="*60)
    print("Scraping complete!")
    print("="*60)


if __name__ == "__main__":
    main()