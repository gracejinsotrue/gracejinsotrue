import requests
import json
import os
from collections import defaultdict
import base64

class GitHubLanguageStats:
    def __init__(self, username, token):
        self.username = username
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
    
    def get_all_repos(self):
        """Get all repositories (public and private) for the user"""
        repos = []
        page = 1
        
        while True:
            url = f'{self.base_url}/user/repos'
            params = {
                'per_page': 100,
                'page': page,
                'type': 'all',
                'sort': 'updated'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
                
            repos.extend(page_repos)
            page += 1
        
        return repos
    
    def get_repo_languages(self, repo_name):
        """Get language statistics for a specific repository"""
        url = f'{self.base_url}/repos/{self.username}/{repo_name}/languages'
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not fetch languages for {repo_name}: {e}")
            return {}
    
    def calculate_language_stats(self, exclude_forks=True, exclude_archived=True):
        """Calculate overall language statistics across all repositories"""
        repos = self.get_all_repos()
        language_stats = defaultdict(int)
        processed_repos = 0
        
        print(f"Found {len(repos)} repositories")
        
        for repo in repos:
            # Skip forks if requested
            if exclude_forks and repo['fork']:
                continue
                
            # Skip archived repos if requested
            if exclude_archived and repo['archived']:
                continue
                
            # Skip empty repositories
            if repo['size'] == 0:
                continue
            
            repo_languages = self.get_repo_languages(repo['name'])
            
            for language, bytes_count in repo_languages.items():
                language_stats[language] += bytes_count
            
            processed_repos += 1
        
        print(f"Processed {processed_repos} repositories")
        return dict(language_stats)
    
    def generate_language_percentages(self, language_stats):
        """Convert byte counts to percentages"""
        total_bytes = sum(language_stats.values())
        
        if total_bytes == 0:
            return {}
        
        percentages = {}
        for language, bytes_count in language_stats.items():
            percentages[language] = (bytes_count / total_bytes) * 100
        
        return percentages
    
    def generate_markdown_stats(self, language_percentages, max_languages=10):
        """Generate markdown table for README"""
        sorted_languages = sorted(language_percentages.items(), 
                                key=lambda x: x[1], reverse=True)
        
        # Take top languages
        top_languages = sorted_languages[:max_languages]
        
        # Generate progress bars using Unicode
        markdown = "## 📊 Language Statistics\n\n"
        
        for language, percentage in top_languages:
            # Create a progress bar
            filled_blocks = int(percentage / 2)  # Scale to 50 chars max
            empty_blocks = 50 - filled_blocks
            
            progress_bar = "█" * filled_blocks + "░" * empty_blocks
            
            markdown += f"**{language}** {percentage:.1f}%\n"
            markdown += f"```\n{progress_bar}\n```\n\n"
        
        return markdown
    
    def generate_svg_chart(self, language_percentages, output_file='language_stats.svg'):
        """Generate an SVG chart of language statistics"""
        sorted_languages = sorted(language_percentages.items(), 
                                key=lambda x: x[1], reverse=True)
        
        # Take top 8 languages for better visibility
        top_languages = sorted_languages[:8]
        
        # GitHub language colors
        colors = {
            'JavaScript': '#f1e05a',
            'Python': '#3572A5',
            'Java': '#b07219',
            'TypeScript': '#2b7489',
            'C++': '#f34b7d',
            'C': '#555555',
            'HTML': '#e34c26',
            'CSS': '#563d7c',
            'PHP': '#4F5D95',
            'Go': '#00ADD8',
            'Ruby': '#701516',
            'Swift': '#ffac45',
            'Kotlin': '#F18E33',
            'Rust': '#dea584',
            'C#': '#239120',
            'Shell': '#89e051',
            'Vue': '#2c3e50',
            'Dart': '#00B4AB',
            'Scala': '#c22d40',
            'R': '#198CE7'
        }
        
        svg_width = 500
        svg_height = 50 + (len(top_languages) * 35)
        
        svg_content = f'''<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <style>
            .language-text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 14px; fill: #24292e; }}
            .percentage-text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 12px; fill: #586069; }}
            .title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 600; fill: #24292e; }}
        </style>
    </defs>
    
    <rect width="100%" height="100%" fill="#ffffff"/>
    <text x="250" y="25" text-anchor="middle" class="title">Most Used Languages</text>
'''
        
        y_position = 50
        bar_height = 20
        max_width = 350
        
        for language, percentage in top_languages:
            bar_width = (percentage / 100) * max_width
            color = colors.get(language, '#586069')
            
            # Draw background bar
            svg_content += f'    <rect x="100" y="{y_position}" width="{max_width}" height="{bar_height}" fill="#f6f8fa" rx="10"/>\n'
            
            # Draw filled bar
            svg_content += f'    <rect x="100" y="{y_position}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="10"/>\n'
            
            # Draw language name
            svg_content += f'    <text x="95" y="{y_position + 15}" text-anchor="end" class="language-text">{language}</text>\n'
            
            # Draw percentage
            svg_content += f'    <text x="460" y="{y_position + 15}" class="percentage-text">{percentage:.1f}%</text>\n'
            
            y_position += 35
        
        svg_content += '</svg>'
        
        with open(output_file, 'w') as f:
            f.write(svg_content)
        
        print(f"SVG chart saved to {output_file}")
        return svg_content

def main():
    # Get configuration from environment variables
    username = os.getenv('GITHUB_REPOSITORY_OWNER')
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("❌ GITHUB_TOKEN environment variable is required")
        print("For local development, create a Personal Access Token at:")
        print("https://github.com/settings/tokens")
        print("Give it 'repo' scope for private repository access")
        return
    
    if not username:
        print("❌ GITHUB_REPOSITORY_OWNER environment variable is required")
        return
    
    print(f"🔍 Analyzing repositories for user: {username}")
    
    # Create analyzer instance
    analyzer = GitHubLanguageStats(username, token)
    
    try:
        # Get language statistics
        print("📊 Fetching repository data...")
        language_stats = analyzer.calculate_language_stats(
            exclude_forks=True, 
            exclude_archived=True
        )
        
        if not language_stats:
            print("❌ No language data found!")
            return
        
        # Calculate percentages
        language_percentages = analyzer.generate_language_percentages(language_stats)
        
        # Generate outputs
        print("📈 Generating visualizations...")
        
        # Generate SVG chart
        svg_content = analyzer.generate_svg_chart(language_percentages)
        
        # Generate markdown stats
        markdown_stats = analyzer.generate_markdown_stats(language_percentages)
        
        # Save markdown stats
        with open('language_stats.md', 'w') as f:
            f.write(markdown_stats)
        
        # Save raw data
        with open('language_stats.json', 'w') as f:
            json.dump({
                'username': username,
                'raw_stats': language_stats,
                'percentages': language_percentages,
                'total_repositories': len(language_stats)
            }, f, indent=2)
        
        print("\n✅ Files generated:")
        print("   📄 language_stats.svg - Visual chart")
        print("   📝 language_stats.md - Markdown table")
        print("   📊 language_stats.json - Raw data")
        
        # Print summary
        print(f"\n📋 Summary:")
        print(f"   🔢 Total languages: {len(language_stats)}")
        print(f"   📊 Top 5 languages:")
        
        sorted_languages = sorted(language_percentages.items(), 
                                key=lambda x: x[1], reverse=True)
        for i, (language, percentage) in enumerate(sorted_languages[:5], 1):
            print(f"      {i}. {language}: {percentage:.1f}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
