#!/usr/bin/env python3
"""
Comprehensive test suite for all NVIDIA NIMs
Tests color extraction, palette generation, and accessibility check services
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

class NIMTestSuite:
    def __init__(self):
        self.base_urls = {
            "color_extraction": "http://localhost:8080",
            "palette_generation": "http://localhost:8081", 
            "accessibility_check": "http://localhost:8082"
        }
        
        self.test_data = {
            "test_images": [
                "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
                "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800"
            ],
            "test_colors": ["#FF5733", "#3498DB", "#2ECC71", "#F39C12"],
            "color_pairs": [
                {"fg": "#000000", "bg": "#FFFFFF"},  # High contrast
                {"fg": "#777777", "bg": "#FFFFFF"},  # Medium contrast
                {"fg": "#CCCCCC", "bg": "#FFFFFF"}   # Low contrast
            ]
        }

    async def test_service_health(self, session: aiohttp.ClientSession, service_name: str, base_url: str) -> Dict[str, Any]:
        """Test service health endpoint"""
        try:
            async with session.get(f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"status": "healthy", "data": data}
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def test_color_extraction(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test color extraction NIM"""
        results = []
        base_url = self.base_urls["color_extraction"]
        
        for i, image_url in enumerate(self.test_data["test_images"]):
            payload = {
                "image_url": image_url,
                "num_colors": 5,
                "min_percentage": 0.05
            }
            
            start_time = time.time()
            try:
                async with session.post(
                    f"{base_url}/extract-colors",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    processing_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        results.append({
                            "test": f"image_{i+1}",
                            "status": "success",
                            "colors_found": result.get("total_colors_found", 0),
                            "algorithm": result.get("algorithm_used", "unknown"),
                            "processing_time": processing_time,
                            "service_time": result.get("processing_time_ms", 0)
                        })
                    else:
                        error_data = await response.text()
                        results.append({
                            "test": f"image_{i+1}",
                            "status": "error",
                            "error": f"HTTP {response.status}: {error_data}"
                        })
                        
            except Exception as e:
                results.append({
                    "test": f"image_{i+1}",
                    "status": "error", 
                    "error": str(e)
                })
        
        return {"service": "color_extraction", "results": results}

    async def test_palette_generation(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test palette generation NIM"""
        results = []
        base_url = self.base_urls["palette_generation"]
        
        palette_types = ["monochromatic", "complementary", "triadic", "analogous"]
        
        for palette_type in palette_types:
            payload = {
                "base_color": "#3498DB",
                "palette_type": palette_type,
                "num_colors": 5,
                "saturation_range": [0.3, 0.9],
                "lightness_range": [0.2, 0.8]
            }
            
            start_time = time.time()
            try:
                async with session.post(
                    f"{base_url}/generate-palette",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    processing_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        results.append({
                            "test": palette_type,
                            "status": "success",
                            "colors_generated": result.get("total_colors", 0),
                            "harmony_score": result.get("harmony_score", 0),
                            "processing_time": processing_time,
                            "service_time": result.get("processing_time_ms", 0)
                        })
                    else:
                        error_data = await response.text()
                        results.append({
                            "test": palette_type,
                            "status": "error",
                            "error": f"HTTP {response.status}: {error_data}"
                        })
                        
            except Exception as e:
                results.append({
                    "test": palette_type,
                    "status": "error",
                    "error": str(e)
                })
        
        return {"service": "palette_generation", "results": results}

    async def test_accessibility_check(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test accessibility check NIM"""
        results = []
        base_url = self.base_urls["accessibility_check"]
        
        # Test individual color pairs
        for i, pair in enumerate(self.test_data["color_pairs"]):
            payload = {
                "foreground_color": pair["fg"],
                "background_color": pair["bg"],
                "text_size": "normal",
                "wcag_level": "AA",
                "check_colorblind": True
            }
            
            start_time = time.time()
            try:
                async with session.post(
                    f"{base_url}/check-accessibility",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    processing_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        results.append({
                            "test": f"pair_{i+1}_{pair['fg']}_{pair['bg']}",
                            "status": "success",
                            "contrast_ratio": result.get("contrast_result", {}).get("ratio", 0),
                            "passes_aa": result.get("contrast_result", {}).get("passes_aa_normal", False),
                            "colorblind_checks": len(result.get("colorblindness_results", [])),
                            "processing_time": processing_time,
                            "service_time": result.get("processing_time_ms", 0)
                        })
                    else:
                        error_data = await response.text()
                        results.append({
                            "test": f"pair_{i+1}",
                            "status": "error",
                            "error": f"HTTP {response.status}: {error_data}"
                        })
                        
            except Exception as e:
                results.append({
                    "test": f"pair_{i+1}",
                    "status": "error",
                    "error": str(e)
                })
        
        # Test palette accessibility
        palette_payload = {
            "colors": self.test_data["test_colors"],
            "wcag_level": "AA"
        }
        
        start_time = time.time()
        try:
            async with session.post(
                f"{base_url}/check-palette-accessibility",
                json=palette_payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                processing_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    results.append({
                        "test": "palette_accessibility",
                        "status": "success",
                        "total_combinations": result.get("total_combinations", 0),
                        "accessible_combinations": result.get("accessible_combinations", 0),
                        "accessibility_score": result.get("accessibility_score", 0),
                        "processing_time": processing_time,
                        "service_time": result.get("processing_time_ms", 0)
                    })
                else:
                    error_data = await response.text()
                    results.append({
                        "test": "palette_accessibility",
                        "status": "error",
                        "error": f"HTTP {response.status}: {error_data}"
                    })
                    
        except Exception as e:
            results.append({
                "test": "palette_accessibility",
                "status": "error",
                "error": str(e)
            })
        
        return {"service": "accessibility_check", "results": results}

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite for all NIMs"""
        print("🚀 Starting NVIDIA NIMs Test Suite")
        print("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoints
            print("\n🔍 Testing Health Endpoints...")
            health_results = {}
            for service_name, base_url in self.base_urls.items():
                print(f"  Testing {service_name}...")
                health_results[service_name] = await self.test_service_health(session, service_name, base_url)
                status = health_results[service_name]["status"]
                print(f"    Status: {status}")
            
            # Run functional tests
            print("\n🧪 Running Functional Tests...")
            
            print("\n  🎨 Testing Color Extraction NIM...")
            color_extraction_results = await self.test_color_extraction(session)
            
            print("  🎭 Testing Palette Generation NIM...")
            palette_generation_results = await self.test_palette_generation(session)
            
            print("  ♿ Testing Accessibility Check NIM...")
            accessibility_results = await self.test_accessibility_check(session)
            
            # Compile results
            results = {
                "timestamp": time.time(),
                "health_checks": health_results,
                "functional_tests": {
                    "color_extraction": color_extraction_results,
                    "palette_generation": palette_generation_results,
                    "accessibility_check": accessibility_results
                }
            }
            
            return results

    def print_results_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of test results"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        # Health check summary
        print("\n🔍 Health Check Results:")
        for service, health in results["health_checks"].items():
            status_icon = "✅" if health["status"] == "healthy" else "❌"
            print(f"  {status_icon} {service}: {health['status']}")
        
        # Functional test summary
        print("\n🧪 Functional Test Results:")
        for service_name, service_results in results["functional_tests"].items():
            print(f"\n  📋 {service_name.replace('_', ' ').title()}:")
            
            total_tests = len(service_results["results"])
            successful_tests = sum(1 for r in service_results["results"] if r["status"] == "success")
            
            print(f"    Total Tests: {total_tests}")
            print(f"    Successful: {successful_tests}")
            print(f"    Failed: {total_tests - successful_tests}")
            print(f"    Success Rate: {successful_tests/total_tests*100:.1f}%")
            
            # Show individual test results
            for test_result in service_results["results"]:
                status_icon = "✅" if test_result["status"] == "success" else "❌"
                test_name = test_result["test"]
                print(f"      {status_icon} {test_name}")
                
                if test_result["status"] == "error":
                    print(f"        Error: {test_result['error']}")
        
        # Overall summary
        all_health_good = all(h["status"] == "healthy" for h in results["health_checks"].values())
        all_tests = []
        for service_results in results["functional_tests"].values():
            all_tests.extend(service_results["results"])
        
        total_functional_tests = len(all_tests)
        successful_functional_tests = sum(1 for t in all_tests if t["status"] == "success")
        
        print("\n🎯 Overall Summary:")
        print(f"  Health Checks: {'✅ All Healthy' if all_health_good else '❌ Some Issues'}")
        print(f"  Functional Tests: {successful_functional_tests}/{total_functional_tests} passed ({successful_functional_tests/total_functional_tests*100:.1f}%)")
        
        if all_health_good and successful_functional_tests == total_functional_tests:
            print("\n🎉 All NIMs are working perfectly! Ready for production deployment.")
        else:
            print("\n⚠️  Some issues detected. Please check the failed tests above.")

async def main():
    """Main test execution"""
    test_suite = NIMTestSuite()
    
    try:
        results = await test_suite.run_all_tests()
        test_suite.print_results_summary(results)
        
        # Save results to file
        with open("nim_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: nim_test_results.json")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    print("🔧 NVIDIA NIMs Test Suite")
    print("Make sure all NIM services are running:")
    print("  - Color Extraction NIM: http://localhost:8080")
    print("  - Palette Generation NIM: http://localhost:8081") 
    print("  - Accessibility Check NIM: http://localhost:8082")
    print()
    
    exit_code = asyncio.run(main())
    exit(exit_code)
