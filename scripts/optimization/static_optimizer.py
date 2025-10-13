"""
Static File Optimizer Script
Consolidates and optimizes static files for web delivery
"""
import os
import shutil
import hashlib
import logging
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StaticFileOptimizer:
    """Static file optimization utility class."""
    
    def __init__(self):
        """Initialize the optimizer with statistics tracking."""
        self.duplicates_found = []
        self.large_files = []
        self.optimization_stats = {
            'files_analyzed': 0,
            'duplicates_removed': 0,
            'space_saved': 0,
            'errors': []
        }
        
        # Static directories to analyze
        self.static_dirs = ['static/', 'main/static/']
    
    def find_duplicate_files(self):
        """Find duplicate files in static directories."""
        file_hashes = defaultdict(list)
        
        logger.info("Scanning for duplicate files...")
        
        for static_dir in self.static_dirs:
            if os.path.exists(static_dir):
                for root, dirs, files in os.walk(static_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_hash = self.get_file_hash(file_path)
                        
                        if file_hash:
                            file_hashes[file_hash].append(file_path)
                            self.optimization_stats['files_analyzed'] += 1
        
        # Find duplicates
        for file_hash, file_paths in file_hashes.items():
            if len(file_paths) > 1:
                self.duplicates_found.append(file_paths)
        
        logger.info(f"Found {len(self.duplicates_found)} groups of duplicate files")
        return self.duplicates_found
    
    def remove_duplicate_files(self):
        """Remove duplicate files, keeping the first occurrence."""
        logger.info("Removing duplicate files...")
        
        for duplicate_group in self.duplicates_found:
            # Keep the first file, remove the rest
            keep_file = duplicate_group[0]
            
            for file_path in duplicate_group[1:]:
                try:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    self.optimization_stats['duplicates_removed'] += 1
                    self.optimization_stats['space_saved'] += file_size
                    
                    logger.info(f"Removed duplicate: {file_path}")
                    
                except Exception as e:
                    error_msg = f"Failed to remove {file_path}: {e}"
                    logger.error(error_msg)
                    self.optimization_stats['errors'].append(error_msg)
    
    def analyze_large_files(self):
        """Analyze files larger than 1MB."""
        large_files = []
        
        logger.info("Analyzing large files...")
        
        for static_dir in self.static_dirs:
            if os.path.exists(static_dir):
                for root, dirs, files in os.walk(static_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        
                        if file_size > 1024 * 1024:  # 1MB
                            large_files.append((file_path, file_size))
        
        self.large_files = large_files
        logger.info(f"Found {len(large_files)} large files")
        return large_files
    
    def optimize_css_files(self):
        """Optimize CSS files by removing unnecessary whitespace."""
        css_files = []
        
        logger.info("Optimizing CSS files...")
        
        for static_dir in self.static_dirs:
            if os.path.exists(static_dir):
                for root, dirs, files in os.walk(static_dir):
                    for file in files:
                        if file.endswith('.css'):
                            file_path = os.path.join(root, file)
                            css_files.append(file_path)
        
        for css_file in css_files:
            try:
                original_size = os.path.getsize(css_file)
                
                # Read CSS content
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic optimization: remove extra whitespace
                optimized_content = ' '.join(content.split())
                
                # Write optimized content
                with open(css_file, 'w', encoding='utf-8') as f:
                    f.write(optimized_content)
                
                new_size = os.path.getsize(css_file)
                savings = original_size - new_size
                
                if savings > 0:
                    self.optimization_stats['space_saved'] += savings
                    logger.info(f"Optimized CSS {css_file}: {original_size} → {new_size} bytes")
                
            except Exception as e:
                error_msg = f"Failed to optimize CSS {css_file}: {e}"
                logger.error(error_msg)
                self.optimization_stats['errors'].append(error_msg)
    
    def optimize_js_files(self):
        """Optimize JavaScript files by removing unnecessary whitespace."""
        js_files = []
        
        logger.info("Optimizing JavaScript files...")
        
        for static_dir in self.static_dirs:
            if os.path.exists(static_dir):
                for root, dirs, files in os.walk(static_dir):
                    for file in files:
                        if file.endswith('.js'):
                            file_path = os.path.join(root, file)
                            js_files.append(file_path)
        
        for js_file in js_files:
            try:
                original_size = os.path.getsize(js_file)
                
                # Read JS content
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic optimization: remove extra whitespace
                optimized_content = ' '.join(content.split())
                
                # Write optimized content
                with open(js_file, 'w', encoding='utf-8') as f:
                    f.write(optimized_content)
                
                new_size = os.path.getsize(js_file)
                savings = original_size - new_size
                
                if savings > 0:
                    self.optimization_stats['space_saved'] += savings
                    logger.info(f"Optimized JS {js_file}: {original_size} → {new_size} bytes")
                
            except Exception as e:
                error_msg = f"Failed to optimize JS {js_file}: {e}"
                logger.error(error_msg)
                self.optimization_stats['errors'].append(error_msg)
    
    def consolidate_static_files(self):
        """Consolidate static files by removing duplicates and optimizing."""
        logger.info("Starting static file consolidation...")
        
        # Find duplicates
        self.find_duplicate_files()
        
        # Remove duplicates
        self.remove_duplicate_files()
        
        # Analyze large files
        self.analyze_large_files()
        
        # Optimize CSS files
        self.optimize_css_files()
        
        # Optimize JS files
        self.optimize_js_files()
        
        logger.info("Static file consolidation completed!")
    
    def get_file_hash(self, file_path):
        """Get MD5 hash of file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None
    
    def get_optimization_report(self):
        """Get optimization statistics."""
        return {
            'files_analyzed': self.optimization_stats['files_analyzed'],
            'duplicates_found': len(self.duplicates_found),
            'duplicates_removed': self.optimization_stats['duplicates_removed'],
            'large_files_found': len(self.large_files),
            'space_saved': self.optimization_stats['space_saved'],
            'errors': self.optimization_stats['errors']
        }
    
    def print_optimization_report(self):
        """Print a formatted optimization report."""
        report = self.get_optimization_report()
        
        print("\n" + "="*60)
        print("STATIC FILE OPTIMIZATION REPORT")
        print("="*60)
        print(f"Files analyzed: {report['files_analyzed']}")
        print(f"Duplicate groups found: {report['duplicates_found']}")
        print(f"Duplicate files removed: {report['duplicates_removed']}")
        print(f"Large files found: {report['large_files_found']}")
        print(f"Total space saved: {report['space_saved']:,} bytes ({report['space_saved']/1024/1024:.2f} MB)")
        
        if report['errors']:
            print(f"\nErrors encountered: {len(report['errors'])}")
            for error in report['errors']:
                print(f"  - {error}")
        
        print("="*60)

def main():
    """Main function to run static file optimization."""
    # Create optimizer instance
    optimizer = StaticFileOptimizer()
    
    # Run optimization
    optimizer.consolidate_static_files()
    
    # Print report
    optimizer.print_optimization_report()

if __name__ == '__main__':
    main()

