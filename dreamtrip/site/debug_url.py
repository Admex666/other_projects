
import urllib.parse

def clean_url(booking_url):
    print(f"DEBUG: Processing URL: {booking_url}")
    
    if not booking_url:
        return ""

    # 1. Handle prf.hn / destination: params
    if "destination:" in booking_url:
        parts = booking_url.split("destination:")
        if len(parts) > 1:
            booking_url = parts[1]
            print(f"DEBUG: Removed destination prefix: {booking_url}")
    
    # 2. Recursive unquote (handle double/triple encoding)
    for i in range(3):
        if "%" not in booking_url:
            break
        try:
            decoded = urllib.parse.unquote(booking_url)
            if decoded == booking_url:
                break
            booking_url = decoded
            print(f"DEBUG: Decoded pass {i+1}: {booking_url}")
        except:
            break
            
    # 3. Cleanup
    booking_url = booking_url.strip()
    
    # 4. Protocol check - VITAL
    # If the URL doesn't start with http/https, the browser WILL treat it as relative (localhost:8000/...)
    if not booking_url.startswith("http"):
        if booking_url.startswith("www."):
             booking_url = "https://" + booking_url
        else:
             # Try to salvage malformed URLs or implicit protocols
             print(f"DEBUG: URL missing protocol: {booking_url}")
             # Heuristic: if it looks like a domain, prepend https://
             if "." in booking_url and "/" in booking_url:
                 booking_url = "https://" + booking_url
                 
    print(f"DEBUG: Final URL: {booking_url}")
    return booking_url

# The problematic URLs likely come in as encoded strings.
# Example from user (stripped of localhost prefix which is browser artifact)
bad_url = "https%3A%2F%2Fwww.hotels.com%2FHotel-Search%3Ftpid%3D4780%26mpe%3D1767090371%26endDate%3D2026-01-25"
clean_url(bad_url)

# Another nasty one
bad_url_2 = "https%253A%252F%252Fwww.booking.com"
clean_url(bad_url_2)
