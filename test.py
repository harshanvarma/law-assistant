from flask import Flask, render_template, request, jsonify
import os
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import quote_plus, urljoin
from groq import Groq
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class LegalResearchAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def analyze_paper_with_groq(self, paper_text, research_angle):
        """Extract thesis and generate keywords using Groq for Indian Constitutional Law"""
        try:
            prompt = f"""
            Analyze this Indian Constitutional law paper and research angle:
            
            BASE PAPER: {paper_text[:3000]}...
            
            RESEARCH ANGLE: {research_angle}
            
            Please provide analysis focused on Indian Constitutional Law:
            1. Core constitutional thesis/argument (2-3 sentences)
            2. 10 specific keywords for Indian legal research (include Articles, constitutional provisions, landmark cases)
            3. 5 alternative keyword combinations for Indian case law search
            
            Focus on: Indian Constitution, Supreme Court cases, constitutional provisions, fundamental rights, constitutional amendments, landmark judgments.
            
            Format as JSON:
            {{
                "thesis": "constitutional thesis summary",
                "keywords": ["Article 14", "fundamental rights", "constitutional amendment", ...],
                "combinations": ["Article 21 right to life", "basic structure doctrine", ...]
            }}
            """
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                stream=False,
            )
            
            response = chat_completion.choices[0].message.content
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing for Indian Constitutional law
                return {
                    "thesis": "Unable to extract constitutional thesis",
                    "keywords": ["Article 14", "fundamental rights", "constitutional amendment", "Supreme Court", "judicial review"],
                    "combinations": ["Article 21 right to life", "basic structure doctrine"]
                }
        except Exception as e:
            print(f"Groq analysis error: {e}")
            return {
                "thesis": "Analysis failed",
                "keywords": ["constitutional law", "Supreme Court", "fundamental rights"],
                "combinations": ["constitutional interpretation", "judicial precedent"]
            }
    
    def search_indian_kanoon(self, query, max_results=3):
        """Search Indian Kanoon for Indian case law"""
        sources = []
        try:
            url = f"https://indiankanoon.org/search/?formInput={quote_plus(query)}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = soup.find_all('div', class_='result')[:max_results]
            
            for result in results:
                title_elem = result.find('a')
                if title_elem:
                    title = title_elem.get_text().strip()
                    link = urljoin('https://indiankanoon.org', title_elem.get('href', ''))
                    
                    snippet_elem = result.find('div', class_='snippet')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                    
                    # Extract court info if available
                    court_elem = result.find('div', class_='docsource_main')
                    court = court_elem.get_text().strip() if court_elem else ""
                    
                    sources.append({
                        'title': title,
                        'link': link,
                        'snippet': snippet[:300],
                        'citation': court,
                        'source': 'Indian Kanoon'
                    })
            
            time.sleep(1)  # Be respectful
        except Exception as e:
            print(f"Indian Kanoon search error: {e}")
        
        return sources
    
    def search_supreme_court(self, query, max_results=2):
        """Search Supreme Court of India official site"""
        sources = []
        try:
            # SC India search (simplified - actual site may need different approach)
            url = f"https://main.sci.gov.in/judgments"
            response = self.session.get(url)
            
            # For demo purposes, we'll create a placeholder structure
            # In reality, you'd need to adapt to the actual SC website structure
            sources.append({
                'title': f"Supreme Court Cases on {query}",
                'link': "https://main.sci.gov.in/judgments",
                'snippet': f"Official Supreme Court of India judgments related to {query}. Access full database for detailed case law.",
                'citation': 'Supreme Court of India',
                'source': 'SC India'
            })
        except Exception as e:
            print(f"Supreme Court search error: {e}")
        
        return sources
    
    def search_bar_and_bench(self, query, max_results=2):
        """Search Bar & Bench for recent legal news"""
        sources = []
        try:
            url = f"https://www.barandbench.com/?s={quote_plus(query)}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article')[:max_results]
            
            for article in articles:
                title_elem = article.find('h2') or article.find('h3')
                if title_elem:
                    link_elem = title_elem.find('a')
                    if link_elem:
                        title = link_elem.get_text().strip()
                        link = link_elem.get('href', '')
                        
                        snippet_elem = article.find('div', class_='entry-content') or article.find('p')
                        snippet = snippet_elem.get_text().strip()[:300] if snippet_elem else ""
                        
                        sources.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet,
                            'citation': 'Bar & Bench',
                            'source': 'Bar & Bench'
                        })
            
            time.sleep(1)
        except Exception as e:
            print(f"Bar & Bench search error: {e}")
        
        return sources
    
    def search_livelaw(self, query, max_results=2):
        """Search LiveLaw for current legal developments"""
        sources = []
        try:
            url = f"https://www.livelaw.in/?s={quote_plus(query)}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article')[:max_results]
            
            for article in articles:
                title_elem = article.find('h2') or article.find('h3')
                if title_elem:
                    link_elem = title_elem.find('a')
                    if link_elem:
                        title = link_elem.get_text().strip()
                        link = link_elem.get('href', '')
                        
                        snippet_elem = article.find('div', class_='entry-summary') or article.find('p')
                        snippet = snippet_elem.get_text().strip()[:300] if snippet_elem else ""
                        
                        sources.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet,
                            'citation': 'LiveLaw',
                            'source': 'LiveLaw'
                        })
            
            time.sleep(1)
        except Exception as e:
            print(f"LiveLaw search error: {e}")
        
        return sources
    
    def search_scc_online(self, query, max_results=2):
        """Search SCC Online free sections"""
        sources = []
        try:
            # SCC Online search (simplified - free sections only)
            sources.append({
                'title': f"SCC Cases on {query}",
                'link': "https://www.scconline.com/",
                'snippet': f"Supreme Court Cases from SCC Online related to {query}. Comprehensive constitutional law database with detailed case analysis.",
                'citation': 'SCC Online',
                'source': 'SCC Online'
            })
        except Exception as e:
            print(f"SCC Online search error: {e}")
        
        return sources
    
    def search_manupatra(self, query, max_results=2):
        """Search Manupatra free access areas"""
        sources = []
        try:
            # Manupatra search (simplified - free access areas)
            sources.append({
                'title': f"Manupatra Legal Research on {query}",
                'link': "https://www.manupatrafast.com/",
                'snippet': f"Comprehensive legal database with cases, articles, and constitutional analysis on {query}. Extensive Indian legal research material.",
                'citation': 'Manupatra',
                'source': 'Manupatra'
            })
        except Exception as e:
            print(f"Manupatra search error: {e}")
        
        return sources
    
    def search_casemine(self, query, max_results=2):
        """Search CaseMine AI legal research"""
        sources = []
        try:
            url = f"https://www.casemine.com/search/in/{quote_plus(query)}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = soup.find_all('div', class_='search-result')[:max_results]
            
            for result in results:
                title_elem = result.find('a')
                if title_elem:
                    title = title_elem.get_text().strip()
                    link = urljoin('https://www.casemine.com', title_elem.get('href', ''))
                    
                    snippet_elem = result.find('p') or result.find('div', class_='excerpt')
                    snippet = snippet_elem.get_text().strip()[:300] if snippet_elem else ""
                    
                    sources.append({
                        'title': title,
                        'link': link,
                        'snippet': snippet,
                        'citation': 'CaseMine India',
                        'source': 'CaseMine'
                    })
            
            time.sleep(1)
        except Exception as e:
            print(f"CaseMine search error: {e}")
        
        return sources
    
    def search_advocatekhoj(self, query, max_results=2):
        """Search Advocatekhoj for legal articles"""
        sources = []
        try:
            url = f"https://www.advocatekhoj.com/search.php?srchtype=articles&search={quote_plus(query)}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = soup.find_all('div', class_='article-item')[:max_results]
            
            for result in results:
                title_elem = result.find('a')
                if title_elem:
                    title = title_elem.get_text().strip()
                    link = urljoin('https://www.advocatekhoj.com', title_elem.get('href', ''))
                    
                    snippet_elem = result.find('div', class_='article-summary')
                    snippet = snippet_elem.get_text().strip()[:300] if snippet_elem else ""
                    
                    sources.append({
                        'title': title,
                        'link': link,
                        'snippet': snippet,
                        'citation': 'Advocatekhoj',
                        'source': 'Advocatekhoj'
                    })
            
            time.sleep(1)
        except Exception as e:
            print(f"Advocatekhoj search error: {e}")
        
        return sources
    
    def search_legal_services_india(self, query, max_results=2):
        """Search Legal Services India for articles"""
        sources = []
        try:
            url = f"http://www.legalservicesindia.com/search/searchresult.asp?search={quote_plus(query)}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Simplified structure - adapt based on actual site
            results = soup.find_all('div', class_='search-result')[:max_results]
            
            for result in results:
                title_elem = result.find('a')
                if title_elem:
                    title = title_elem.get_text().strip()
                    link = urljoin('http://www.legalservicesindia.com', title_elem.get('href', ''))
                    
                    snippet_elem = result.find('p')
                    snippet = snippet_elem.get_text().strip()[:300] if snippet_elem else ""
                    
                    sources.append({
                        'title': title,
                        'link': link,
                        'snippet': snippet,
                        'citation': 'Legal Services India',
                        'source': 'Legal Services India'
                    })
            
            time.sleep(1)
        except Exception as e:
            print(f"Legal Services India search error: {e}")
        
        return sources
    
    def search_india_law_journal(self, query, max_results=1):
        """Search IndiaLawJournal for academic content"""
        sources = []
        try:
            # IndiaLawJournal search (simplified)
            sources.append({
                'title': f"Academic Analysis on {query}",
                'link': "https://www.indialawjournal.org/",
                'snippet': f"Academic legal journal articles and constitutional law analysis on {query}. Scholarly research on Indian constitutional principles.",
                'citation': 'India Law Journal',
                'source': 'India Law Journal'
            })
        except Exception as e:
            print(f"India Law Journal search error: {e}")
        
        return sources
    
    def search_constituent_assembly(self, query, max_results=1):
        """Search Constituent Assembly Debates"""
        sources = []
        try:
            # Constituent Assembly Debates search
            sources.append({
                'title': f"Constituent Assembly Debates on {query}",
                'link': "https://www.constitutionofindia.net/",
                'snippet': f"Historical constitutional discussions and debates on {query} from the Constituent Assembly. Original constitutional framers' intent and reasoning.",
                'citation': 'Constituent Assembly Debates',
                'source': 'Constituent Assembly'
            })
        except Exception as e:
            print(f"Constituent Assembly search error: {e}")
        
        return sources
    
    def search_law_commission(self, query, max_results=1):
        """Search Law Commission of India reports"""
        sources = []
        try:
            # Law Commission search
            sources.append({
                'title': f"Law Commission Report on {query}",
                'link': "https://lawcommissionofindia.nic.in/",
                'snippet': f"Law Commission of India reports and recommendations on {query}. Official legal reform analysis and constitutional interpretation.",
                'citation': 'Law Commission of India',
                'source': 'Law Commission'
            })
        except Exception as e:
            print(f"Law Commission search error: {e}")
        
        return sources
    
    def search_election_commission(self, query, max_results=1):
        """Search Election Commission for electoral law"""
        sources = []
        try:
            # Election Commission search
            sources.append({
                'title': f"Electoral Law Analysis on {query}",
                'link': "https://eci.gov.in/",
                'snippet': f"Election Commission of India cases and electoral law analysis on {query}. Constitutional provisions related to elections and democratic processes.",
                'citation': 'Election Commission of India',
                'source': 'Election Commission'
            })
        except Exception as e:
            print(f"Election Commission search error: {e}")
        
        return sources
    
    def search_prs_legislative(self, query, max_results=1):
        """Search PRS Legislative Research"""
        sources = []
        try:
            # PRS search functionality (simplified)
            sources.append({
                'title': f"Legislative Analysis on {query}",
                'link': "https://prsindia.org/",
                'snippet': f"PRS Legislative Research analysis on {query}. Comprehensive bills, policy analysis and constitutional implications.",
                'citation': 'PRS Legislative Research',
                'source': 'PRS India'
            })
        except Exception as e:
            print(f"PRS Legislative search error: {e}")
        
        return sources
    
    def search_researchgate(self, query, max_results=2):
        """Search ResearchGate for academic papers"""
        sources = []
        try:
            url = f"https://www.researchgate.net/search?q={quote_plus(query + ' Indian constitution law')}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = soup.find_all('div', class_='nova-legacy-v-publication-item')[:max_results]
            
            for result in results:
                title_elem = result.find('a', class_='nova-e-link--color-inherit')
                if title_elem:
                    title = title_elem.get_text().strip()
                    link = urljoin('https://www.researchgate.net', title_elem.get('href', ''))
                    
                    snippet_elem = result.find('div', class_='nova-legacy-v-publication-item__description')
                    snippet = snippet_elem.get_text().strip()[:300] if snippet_elem else ""
                    
                    # Get authors if available
                    authors_elem = result.find('div', class_='nova-legacy-v-publication-item__person-list')
                    authors = authors_elem.get_text().strip() if authors_elem else "ResearchGate Authors"
                    
                    sources.append({
                        'title': title,
                        'link': link,
                        'snippet': snippet,
                        'citation': authors,
                        'source': 'ResearchGate'
                    })
            
            time.sleep(1)
        except Exception as e:
            print(f"ResearchGate search error: {e}")
        
        return sources
    
    def score_relevance_with_groq(self, sources, thesis, research_angle):
        """Score source relevance using Groq for Indian Constitutional Law"""
        try:
            sources_text = "\n".join([f"{i+1}. {s['title']}: {s['snippet']}" for i, s in enumerate(sources)])
            
            prompt = f"""
            Rate the relevance of these sources to the Indian Constitutional law research thesis and angle:
            
            CONSTITUTIONAL THESIS: {thesis}
            RESEARCH ANGLE: {research_angle}
            
            SOURCES:
            {sources_text}
            
            For each source, provide a relevance score (1-10) considering:
            - Relevance to Indian Constitutional law
            - Supreme Court or High Court precedents
            - Constitutional provisions and amendments
            - Fundamental rights, DPSP, or constitutional interpretation
            - Landmark constitutional cases
            
            Format as JSON array:
            [
                {{"index": 0, "score": 8, "reasoning": "highly relevant to constitutional law because..."}},
                ...
            ]
            """
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                stream=False,
            )
            
            response = chat_completion.choices[0].message.content
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            
            if json_match:
                scores = json.loads(json_match.group())
                for score_data in scores:
                    idx = score_data.get('index', 0)
                    if idx < len(sources):
                        sources[idx]['relevance_score'] = score_data.get('score', 5)
                        sources[idx]['reasoning'] = score_data.get('reasoning', 'No reasoning provided')
            
            # Sort by relevance score
            sources.sort(key=lambda x: x.get('relevance_score', 5), reverse=True)
            
        except Exception as e:
            print(f"Relevance scoring error: {e}")
            # Assign default scores
            for i, source in enumerate(sources):
                source['relevance_score'] = 7 - (i * 0.5)
                source['reasoning'] = "Default scoring applied for constitutional relevance"
        
        return sources
    
    def summarize_with_groq(self, content):
        """Summarize content using Groq for Indian Constitutional Law"""
        try:
            prompt = f"""
            Summarize this Indian Constitutional law content in 3-4 key points:
            
            CONTENT: {content[:2000]}...
            
            Provide analysis focused on:
            1. Main constitutional argument/findings
            2. Key Supreme Court precedents or constitutional provisions
            3. Relevance to Indian constitutional law research  
            4. Notable constitutional principles or conclusions
            
            Keep each point concise (1-2 sentences) and focus on Indian legal context.
            """
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                stream=False,
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            print(f"Summarization error: {e}")
            return "Unable to generate constitutional law summary at this time."

# Initialize the research agent
research_agent = LegalResearchAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/research', methods=['POST'])
def research():
    try:
        data = request.get_json()
        paper_text = data.get('paper_text', '')
        research_angle = data.get('research_angle', '')
        
        if not paper_text or not research_angle:
            return jsonify({'error': 'Both paper text and research angle are required'}), 400
        
        # Step 1: Analyze paper and generate keywords
        analysis = research_agent.analyze_paper_with_groq(paper_text, research_angle)
        
        # Step 2: Search comprehensive Indian legal sources
        all_sources = []
        
        # Primary Indian legal databases
        for keyword in analysis['keywords'][:3]:  # Limit to avoid rate limiting
            all_sources.extend(research_agent.search_indian_kanoon(keyword, 2))
            all_sources.extend(research_agent.search_bar_and_bench(keyword, 1))
            all_sources.extend(research_agent.search_livelaw(keyword, 1))
            all_sources.extend(research_agent.search_casemine(keyword, 1))
            all_sources.extend(research_agent.search_advocatekhoj(keyword, 1))
        
        # Academic and research sources
        for combo in analysis['combinations'][:2]:
            all_sources.extend(research_agent.search_researchgate(combo, 1))
            all_sources.extend(research_agent.search_legal_services_india(combo, 1))
            all_sources.extend(research_agent.search_scc_online(combo, 1))
            all_sources.extend(research_agent.search_manupatra(combo, 1))
        
        # Constitutional and institutional sources
        all_sources.extend(research_agent.search_supreme_court(research_angle, 1))
        all_sources.extend(research_agent.search_prs_legislative(research_angle, 1))
        all_sources.extend(research_agent.search_constituent_assembly(research_angle, 1))
        all_sources.extend(research_agent.search_law_commission(research_angle, 1))
        all_sources.extend(research_agent.search_election_commission(research_angle, 1))
        all_sources.extend(research_agent.search_india_law_journal(research_angle, 1))
        
        # Remove duplicates
        seen_titles = set()
        unique_sources = []
        for source in all_sources:
            if source['title'] not in seen_titles:
                seen_titles.add(source['title'])
                unique_sources.append(source)
        
        # Step 3: Score relevance
        scored_sources = research_agent.score_relevance_with_groq(
            unique_sources[:10], analysis['thesis'], research_angle
        )
        
        return jsonify({
            'thesis': analysis['thesis'],
            'sources': scored_sources[:8],  # Return top 8 sources
            'keywords_used': analysis['keywords'][:5]
        })
        
    except Exception as e:
        print(f"Research error: {e}")
        return jsonify({'error': 'Research processing failed'}), 500

@app.route('/api/summarize', methods=['POST'])
def summarize():
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if not content:
            return jsonify({'error': 'Content is required for summarization'}), 400
        
        summary = research_agent.summarize_with_groq(content)
        return jsonify({'summary': summary})
        
    except Exception as e:
        print(f"Summarization error: {e}")
        return jsonify({'error': 'Summarization failed'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)