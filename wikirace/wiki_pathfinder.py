import asyncio
import aiohttp
import sys
import time
from collections import deque
from bs4 import BeautifulSoup

class WikipediaAPI:
    def __init__(self, session, lang="en"):
        self.base_url = f"https://{lang}.wikipedia.org/w/api.php"
        self.session = session
        self.headers = {
            "User-Agent": "WikiPathfinder/1.0 (https://your-email@example.com) aiohttp/3.x"
        }

    async def resolve_title(self, title):
        """Resolves redirects and normalizes the title."""
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "redirects": 1
        }
        try:
            async with self.session.get(self.base_url, params=params, headers=self.headers) as resp:
                data = await resp.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id in pages:
                    if page_id == "-1":
                        return None # Page not found
                    return pages[page_id].get("title")
        except Exception as e:
            print(f"Error resolving title {title}: {e}", file=sys.stderr)
            return title
        return title

    async def get_links(self, title, visible_only=False):
        """Gets outgoing links from a page."""
        if visible_only:
            return await self._get_visible_links(title)
            
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "links",
            "pllimit": "max",
            "plnamespace": 0
        }
        links = []
        while True:
            try:
                async with self.session.get(self.base_url, params=params, headers=self.headers) as resp:
                    data = await resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page_id in pages:
                        page_links = pages[page_id].get("links", [])
                        links.extend([l["title"] for l in page_links])
                    
                    if "continue" in data:
                        params.update(data["continue"])
                    else:
                        break
            except Exception as e:
                print(f"Error fetching links for {title}: {e}", file=sys.stderr)
                break
        return links

    async def _get_visible_links(self, title):
        """Fetches HTML and extracts links NOT in navboxes/infoboxes."""
        params = {
            "action": "parse",
            "format": "json",
            "page": title,
            "prop": "text",
            "disableeditsection": 1,
            "disablestylededuplication": 1
        }
        try:
            async with self.session.get(self.base_url, params=params, headers=self.headers) as resp:
                data = await resp.json()
                html_content = data.get("parse", {}).get("text", {}).get("*", "")
                if not html_content:
                    return []
                
                soup = BeautifulSoup(html_content, "html.parser")
                content_div = soup.find("div", class_="mw-parser-output")
                if not content_div:
                    content_div = soup

                # Remove non-prose elements
                for unwanted in content_div.find_all(class_=["navbox", "infobox", "sidebar", "vertical-navbox", "metadata", "reflist", "ambox"]):
                    unwanted.decompose()

                links = {}
                for a in content_div.find_all("a", href=True):
                    # Wikipedia internal links start with /wiki/ and don't contain : (except Category: etc which we usually skip)
                    href = a["href"]
                    if href.startswith("/wiki/") and ":" not in href[6:]:
                        title = a.get("title") or href[6:].replace("_", " ")
                        text = a.get_text().strip()
                        # Store the first text encountered for each title
                        if title not in links:
                            links[title] = text
                
                return links # Return dict {title: text}
        except Exception as e:
            print(f"Error parsing visible links for {title}: {e}", file=sys.stderr)
            return {}

    async def get_backlinks(self, title, visible_only=False):
        """Gets pages linking to this page (backlinks)."""
        params = {
            "action": "query",
            "format": "json",
            "list": "backlinks",
            "bltitle": title,
            "bllimit": "max",
            "blnamespace": 0
        }
        backlinks = []
        while True:
            try:
                async with self.session.get(self.base_url, params=params, headers=self.headers) as resp:
                    data = await resp.json()
                    bl = data.get("query", {}).get("backlinks", [])
                    backlinks.extend([l["title"] for l in bl])
                    
                    if "continue" in data:
                        params.update(data["continue"])
                    else:
                        break
            except Exception as e:
                print(f"Error fetching backlinks for {title}: {e}", file=sys.stderr)
                break
        return backlinks

    async def get_link_text(self, source, target):
        """Fetches the anchor text for a specific link on a source page."""
        links_data = await self.get_links(source, visible_only=True)
        # links version from get_links(visible_only=True) is a dict {title: text}
        if isinstance(links_data, dict):
            return links_data.get(target, target)
        return target

class ShortestPathFinder:
    def __init__(self, start, end, lang="en", max_concurrency=10, visible_only=False):
        self.start = start
        self.end = end
        self.lang = lang
        self.visible_only = visible_only
        self.semaphore = asyncio.Semaphore(max_concurrency)
        
        # Forward search state
        self.forward_queue = deque([start])
        self.forward_parent = {start: None}
        self.forward_text = {start: ""} # Store the text on the link that led here
        
        # Backward search state
        self.backward_queue = deque([end])
        self.backward_parent = {end: None}
        self.backward_text = {end: ""} # Store the text on the link that led here (reversed role)

    async def find_path(self):
        async with aiohttp.ClientSession() as session:
            api = WikipediaAPI(session, self.lang)
            
            # Resolve titles first
            print(f"Resolving titles...")
            resolved_start = await api.resolve_title(self.start)
            resolved_end = await api.resolve_title(self.end)
            
            if not resolved_start or not resolved_end:
                print(f"Error: Could not find one of the articles.")
                if not resolved_start: print(f" - '{self.start}' not found.")
                if not resolved_end: print(f" - '{self.end}' not found.")
                return None

            if resolved_start != self.start or resolved_end != self.end:
                print(f"Normalized: '{self.start}' -> '{resolved_start}'")
                print(f"Normalized: '{self.end}' -> '{resolved_end}'")
            
            self.start = resolved_start
            self.end = resolved_end
            
            # Reset state with resolved titles
            self.forward_queue = deque([self.start])
            self.forward_parent = {self.start: None}
            self.forward_text = {self.start: ""}
            self.backward_queue = deque([self.end])
            self.backward_parent = {self.end: None}
            self.backward_text = {self.end: ""}

            if self.start == self.end:
                return [(self.start, "")]

            mode_str = " (Visible Links Only)" if self.visible_only else ""
            print(f"Searching for shortest path from '{self.start}' to '{self.end}'{mode_str}...")
            
            step = 0
            while self.forward_queue and self.backward_queue:
                step += 1
                
                # Expand the smaller frontier for better performance
                if len(self.forward_queue) <= len(self.backward_queue):
                    print(f"--- Step {step}: Expanding forward ({len(self.forward_queue)} nodes) ---")
                    intersection = await self._expand_forward(api)
                else:
                    print(f"--- Step {step}: Expanding backward ({len(self.backward_queue)} nodes) ---")
                    intersection = await self._expand_backward(api)
                
                if intersection:
                    path_data = self._reconstruct_path(intersection)
                    print(f"Resolving link texts for the final path...")
                    return await self._resolve_missing_texts(api, path_data)
                
            return None

    async def _resolve_missing_texts(self, api, path_data):
        resolved_path = []
        for i, (title, link_text) in enumerate(path_data):
            if i == 0:
                resolved_path.append((title, ""))
            elif link_text == "(via backlink)":
                # Fetch actual anchor text from the previous node
                source = resolved_path[i-1][0]
                actual_text = await api.get_link_text(source, title)
                resolved_path.append((title, actual_text))
            else:
                resolved_path.append((title, link_text))
        return resolved_path

    async def _expand_forward(self, api):
        nodes_to_expand = len(self.forward_queue)
        tasks = []
        for _ in range(nodes_to_expand):
            current = self.forward_queue.popleft()
            tasks.append(self._process_forward_node(api, current))
            
        results = await asyncio.gather(*tasks)
        for intersection in results:
            if intersection:
                return intersection
        return None

    async def _process_forward_node(self, api, current):
        async with self.semaphore:
            links_data = await api.get_links(current, visible_only=self.visible_only)
        
        # links_data can be a list (from query API) or dict (from parse API)
        if isinstance(links_data, dict):
            links = links_data.keys()
        else:
            links = links_data
            
        for link in links:
            if link not in self.forward_parent:
                self.forward_parent[link] = current
                self.forward_text[link] = links_data[link] if isinstance(links_data, dict) else link
                self.forward_queue.append(link)
                if link in self.backward_parent:
                    return link
        return None

    async def _expand_backward(self, api):
        nodes_to_expand = len(self.backward_queue)
        tasks = []
        for _ in range(nodes_to_expand):
            current = self.backward_queue.popleft()
            tasks.append(self._process_backward_node(api, current))
            
        results = await asyncio.gather(*tasks)
        for intersection in results:
            if intersection:
                return intersection
        return None

    async def _process_backward_node(self, api, current):
        async with self.semaphore:
            # We always use all backlinks because verifying visibility for thousands of sources is prohibitive.
            backlinks = await api.get_backlinks(current, visible_only=False)
        for backlink in backlinks:
            if backlink not in self.backward_parent:
                self.backward_parent[backlink] = current
                # Since these are backlinks, 'backlink' is the source page linking to 'current'.
                # We don't have the anchor text easily available for backlinks.
                self.backward_text[backlink] = "(via backlink)"
                self.backward_queue.append(backlink)
                if backlink in self.forward_parent:
                    return backlink
        return None

    def _reconstruct_path(self, intersection):
        # Reconstruct path from forward_parent and backward_parent
        # Returns a list of (title, link_text_from_previous_node)
        path = []
        
        # Part island 1: Start -> Intersection
        curr = intersection
        while curr:
            path.append((curr, self.forward_text[curr]))
            curr = self.forward_parent[curr]
        path.reverse()
        
        # Part island 2: Intersection -> End
        # The backward_parent[intersection] is the node that was "linked to" by some page 
        # in the backward search. Wait, backward search: we start from 'end', 
        # find things that link TO it. So parent of 'end' is 'None'.
        # A node 'X' links to 'end'. Then 'X' is added to backward frontier.
        # Its parent is 'end'.
        
        curr = self.backward_parent[intersection]
        while curr:
            path.append((curr, self.backward_text[curr]))
            curr = self.backward_parent[curr]
            
        return path

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Find the shortest path between two Wikipedia articles.")
    parser.add_argument("start", help="Start article title")
    parser.add_argument("end", help="End article title")
    parser.add_argument("--visible-only", action="store_true", help="Only consider links in the main text (no navboxes/infoboxes)")
    
    args = parser.parse_args()
    
    start_time = time.time()
    finder = ShortestPathFinder(args.start, args.end, visible_only=args.visible_only)
    path_data = await finder.find_path()
    end_time = time.time()
    
    if path_data:
        print("\nShortest path found:")
        for i, (title, link_text) in enumerate(path_data):
            if i == 0:
                print(f"  {title}")
            else:
                display_text = f" (link text: '{link_text}')" if link_text and link_text != title else ""
                print(f"   -> {title}{display_text}")
        
        print(f"\nDistance: {len(path_data) - 1} clicks")
    else:
        print("\nNo path found.")
        
    print(f"Time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
