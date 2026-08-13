
import urllib.parse

def clean_url(booking_url):
    print(f"Original: {booking_url}")
    
    # 1. Handle prf.hn / destination: params
    if "destination:" in booking_url:
        parts = booking_url.split("destination:")
        if len(parts) > 1:
            booking_url = parts[1]
            print(f"After destination split: {booking_url}")
    
    # 2. Recursive unquote
    for i in range(3):
        if "%" not in booking_url:
            break
        try:
            decoded = urllib.parse.unquote(booking_url)
            if decoded == booking_url:
                break
            booking_url = decoded
            print(f"After unquote pass {i+1}: {booking_url}")
        except:
            break
            
    # 3. Cleanup and Protocol check
    booking_url = booking_url.strip()
    
    if booking_url.startswith("www."):
            booking_url = "https://" + booking_url
            print(f"After www fix: {booking_url}")
            
    return booking_url

# Test case 1: The hotels.com encoded link
url1 = "https%3A%2F%2Fwww.hotels.com%2FHotel-Search%3Ftpid%3D4780%26mpe%3D1767090371"
print(f"Final 1: {clean_url(url1)}")

# Test case 2: Embedded destination + encoded
url2 = "https://prf.hn/click/camref:1100lq/destination:https%3A%2F%2Fwww.booking.com"
print(f"Final 2: {clean_url(url2)}")

# Test case 3: Triple encoded
url3 = "https%253A%252F%252Fexample.com"
print(f"Final 3: {clean_url(url3)}")
