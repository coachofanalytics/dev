"""
Image Optimizer Script
Optimizes images for web delivery while maintaining quality
"""
import os
import logging
from PIL import Image
from django.conf import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageOptimizer:
    """Image optimization utility class."""
    
    def __init__(self):
        """Initialize the optimizer with statistics tracking."""
        self.optimization_stats = {
            'files_processed': 0,
            'total_size_before': 0,
            'total_size_after': 0,
            'files_optimized': 0,
            'errors': []
        }
        
        # Optimization settings
        self.quality = 85
        self.max_width = 800
        self.max_height = 600
    
    def compress_image(self, input_path, output_path=None, quality=None):
        """Compress an image file."""
        if output_path is None:
            output_path = input_path
            
        if quality is None:
            quality = self.quality
            
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.width > self.max_width or img.height > self.max_height:
                    img.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
                
                # Save with compression
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                
                # Update stats
                self.optimization_stats['files_processed'] += 1
                self.optimization_stats['files_optimized'] += 1
                
                logger.info(f"Compressed {input_path}: {os.path.getsize(input_path)} bytes")
                
        except Exception as e:
            error_msg = f"Failed to compress {input_path}: {e}"
            logger.error(error_msg)
            self.optimization_stats['errors'].append(error_msg)
    
    def optimize_profile_images(self):
        """Optimize all profile images."""
        profile_dir = 'main/static/main/img/profile/'
        
        if not os.path.exists(profile_dir):
            logger.warning(f"Profile directory not found: {profile_dir}")
            return
            
        logger.info(f"Optimizing profile images in {profile_dir}")
        
        for filename in os.listdir(profile_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(profile_dir, filename)
                
                # Get original size
                original_size = os.path.getsize(file_path)
                self.optimization_stats['total_size_before'] += original_size
                
                # Compress image
                self.compress_image(file_path)
                
                # Get new size
                new_size = os.path.getsize(file_path)
                self.optimization_stats['total_size_after'] += new_size
                
                logger.info(f"Optimized {filename}: {original_size} → {new_size} bytes")
    
    def optimize_service_images(self):
        """Optimize all service images."""
        service_dir = 'main/static/main/img/service/'
        
        if not os.path.exists(service_dir):
            logger.warning(f"Service directory not found: {service_dir}")
            return
            
        logger.info(f"Optimizing service images in {service_dir}")
        
        for filename in os.listdir(service_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(service_dir, filename)
                
                # Get original size
                original_size = os.path.getsize(file_path)
                self.optimization_stats['total_size_before'] += original_size
                
                # Compress image
                self.compress_image(file_path)
                
                # Get new size
                new_size = os.path.getsize(file_path)
                self.optimization_stats['total_size_after'] += new_size
                
                logger.info(f"Optimized {filename}: {original_size} → {new_size} bytes")
    
    def optimize_all_images(self):
        """Optimize all images in the application."""
        logger.info("Starting image optimization process...")
        
        # Optimize profile images
        self.optimize_profile_images()
        
        # Optimize service images
        self.optimize_service_images()
        
        # Optimize other image directories
        other_dirs = [
            'main/static/main/img/',
            'static/img/',
            'static/images/'
        ]
        
        for img_dir in other_dirs:
            if os.path.exists(img_dir):
                self.optimize_directory(img_dir)
        
        logger.info("Image optimization process completed!")
    
    def optimize_directory(self, directory):
        """Optimize all images in a directory."""
        if not os.path.exists(directory):
            return
            
        logger.info(f"Optimizing images in {directory}")
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    file_path = os.path.join(root, filename)
                    
                    # Get original size
                    original_size = os.path.getsize(file_path)
                    self.optimization_stats['total_size_before'] += original_size
                    
                    # Compress image
                    self.compress_image(file_path)
                    
                    # Get new size
                    new_size = os.path.getsize(file_path)
                    self.optimization_stats['total_size_after'] += new_size
                    
                    logger.info(f"Optimized {filename}: {original_size} → {new_size} bytes")
    
    def get_optimization_report(self):
        """Get optimization statistics."""
        total_savings = self.optimization_stats['total_size_before'] - self.optimization_stats['total_size_after']
        savings_percentage = (total_savings / self.optimization_stats['total_size_before']) * 100 if self.optimization_stats['total_size_before'] > 0 else 0
        
        return {
            'files_processed': self.optimization_stats['files_processed'],
            'files_optimized': self.optimization_stats['files_optimized'],
            'total_size_before': self.optimization_stats['total_size_before'],
            'total_size_after': self.optimization_stats['total_size_after'],
            'total_savings': total_savings,
            'savings_percentage': savings_percentage,
            'errors': self.optimization_stats['errors']
        }
    
    def print_optimization_report(self):
        """Print a formatted optimization report."""
        report = self.get_optimization_report()
        
        print("\n" + "="*60)
        print("IMAGE OPTIMIZATION REPORT")
        print("="*60)
        print(f"Files processed: {report['files_processed']}")
        print(f"Files optimized: {report['files_optimized']}")
        print(f"Total size before: {report['total_size_before']:,} bytes ({report['total_size_before']/1024/1024:.2f} MB)")
        print(f"Total size after: {report['total_size_after']:,} bytes ({report['total_size_after']/1024/1024:.2f} MB)")
        print(f"Total savings: {report['total_savings']:,} bytes ({report['total_savings']/1024/1024:.2f} MB)")
        print(f"Savings percentage: {report['savings_percentage']:.1f}%")
        
        if report['errors']:
            print(f"\nErrors encountered: {len(report['errors'])}")
            for error in report['errors']:
                print(f"  - {error}")
        
        print("="*60)

def main():
    """Main function to run image optimization."""
    # Create optimizer instance
    optimizer = ImageOptimizer()
    
    # Run optimization
    optimizer.optimize_all_images()
    
    # Print report
    optimizer.print_optimization_report()

if __name__ == '__main__':
    main()
