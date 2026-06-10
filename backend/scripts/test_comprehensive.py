"""
Comprehensive Test Script for Women Health Expert with Groq Cloud

This script tests the complete system including:
- RAG retrieval
- Response generation with Groq GPT OSS 20B
- Safety enforcement
- Conversation management
- Red flag detection

All queries and responses are logged to test_results.txt
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from generation import Generator
from retrieval import ProductionRetriever

# Load environment from backend/env file
env_path = Path(__file__).parent.parent / 'env'
load_dotenv(dotenv_path=env_path)


class ComprehensiveTest:
    """Comprehensive testing suite for the Women Health Expert chatbot."""
    
    def __init__(self):
        """Initialize test suite."""
        self.results = []
        self.output_file = Path(__file__).parent / "test_results.txt"
        
        # Initialize components
        print("🔧 Initializing components...")
        self.retriever = ProductionRetriever(
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_index_name=os.getenv('PINECONE_INDEX_NAME'),
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        self.generator = Generator(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            retriever=self.retriever
        )
        
        print(f"✓ Using Groq model: {self.generator.generation_model}")
        print(f"✓ Using enforcer model: {self.generator.enforcer_model}")
        print(f"✓ Results will be saved to: {self.output_file}")
        print()
    
    def log(self, message: str):
        """Log message to results."""
        self.results.append(message)
        print(message)
    
    async def test_query(self, query: str, description: str, use_rag: bool = True):
        """Test a single query and log results."""
        self.log("=" * 80)
        self.log(f"TEST: {description}")
        self.log("=" * 80)
        self.log(f"Query: {query}")
        self.log(f"RAG Enabled: {use_rag}")
        self.log("-" * 80)
        
        try:
            # Generate response
            response, metadata = await self.generator.generate_response(
                user_message=query,
                use_rag=use_rag
            )
            
            # Log response
            self.log(f"Response:\n{response}")
            self.log("-" * 80)
            
            # Log metadata
            self.log("Metadata:")
            self.log(f"  - RAG Used: {metadata.get('rag_used', False)}")
            self.log(f"  - Enforcer Used: {metadata.get('enforcer_used', False)}")
            self.log(f"  - Red Flags: {metadata.get('red_flags_detected', [])}")
            self.log(f"  - Safety Violations: {len(metadata.get('safety_violations', []))}")
            self.log(f"  - Clarification Needed: {metadata.get('clarification_needed', False)}")
            
            if 'escalation_level' in metadata:
                self.log(f"  - Escalation Level: {metadata['escalation_level']}")
            
            self.log("-" * 80)
            self.log("✅ Test PASSED")
            
        except Exception as e:
            self.log(f"❌ Test FAILED: {str(e)}")
            self.log("-" * 80)
        
        # CRITICAL: Clear conversation history after each test to prevent context confusion
        self.generator.clear_conversation()
        
        self.log("\n")
    
    async def run_all_tests(self):
        """Run comprehensive test suite."""
        self.log("=" * 80)
        self.log("WOMEN HEALTH EXPERT - COMPREHENSIVE TEST SUITE")
        self.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Model: Groq Cloud - {self.generator.generation_model}")
        self.log("=" * 80)
        self.log("\n")
        
        # Test 1: Basic health query
        await self.test_query(
            query="What are the common symptoms of PCOS?",
            description="Basic Health Query - PCOS Symptoms",
            use_rag=True
        )
        
        # Test 2: Menstrual health
        await self.test_query(
            query="I have irregular periods. What could be causing this?",
            description="Menstrual Health Query",
            use_rag=True
        )
        
        # Test 3: Pregnancy-related query
        await self.test_query(
            query="I'm pregnant and experiencing morning sickness. What can I do?",
            description="Pregnancy Query - Morning Sickness",
            use_rag=True
        )
        
        # Test 4: Red flag - severe pain
        await self.test_query(
            query="I have severe abdominal pain and heavy bleeding",
            description="Red Flag Test - Severe Symptoms",
            use_rag=True
        )
        
        # Test 5: Red flag - post-menopausal bleeding
        await self.test_query(
            query="I'm 55 and started bleeding again after menopause",
            description="Red Flag Test - Post-Menopausal Bleeding",
            use_rag=True
        )
        
        # Test 6: Mental health
        await self.test_query(
            query="I've been feeling very anxious and depressed lately",
            description="Mental Health Query",
            use_rag=True
        )
        
        # Test 7: Contraception
        await self.test_query(
            query="What are the different types of birth control available?",
            description="Contraception Information",
            use_rag=True
        )
        
        # Test 8: Menopause
        await self.test_query(
            query="What are the signs of menopause and how can I manage symptoms?",
            description="Menopause Query",
            use_rag=True
        )
        
        # Test 9: Nutrition and supplements
        await self.test_query(
            query="What vitamins should I take for better reproductive health?",
            description="Nutrition and Supplements",
            use_rag=True
        )
        
        # Test 10: Vague query (should trigger clarification)
        await self.test_query(
            query="I feel weird",
            description="Vague Query - Clarification Test",
            use_rag=True
        )
        
        # Test 11: Follow-up in conversation
        await self.test_query(
            query="Can you tell me more about the symptoms?",
            description="Follow-up Query - Conversation Context",
            use_rag=True
        )
        
        # Test 12: Without RAG
        await self.test_query(
            query="What is endometriosis?",
            description="Query Without RAG",
            use_rag=False
        )
        
        # Test 13: Breast health
        await self.test_query(
            query="I found a lump in my breast. What should I do?",
            description="Breast Health - Urgent Concern",
            use_rag=True
        )
        
        # Test 14: UTI symptoms
        await self.test_query(
            query="I have burning sensation when urinating and frequent urge to pee",
            description="UTI Symptoms Query",
            use_rag=True
        )
        
        # Test 15: Lifestyle and exercise
        await self.test_query(
            query="What exercises are safe during pregnancy?",
            description="Exercise During Pregnancy",
            use_rag=True
        )
        
        # Summary
        self.log("=" * 80)
        self.log("TEST SUITE COMPLETED")
        self.log("=" * 80)
        self.log(f"Total Tests: 15")
        self.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("=" * 80)
        
        # Save to file
        self.save_results()
    
    def save_results(self):
        """Save results to text file."""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.results))
            print(f"\n✅ Results saved to: {self.output_file}")
        except Exception as e:
            print(f"\n❌ Error saving results: {e}")


async def main():
    """Main test execution."""
    print("=" * 80)
    print("WOMEN HEALTH EXPERT - COMPREHENSIVE TEST SUITE")
    print("Testing Groq Cloud Integration with GPT OSS 20B")
    print("=" * 80)
    print()
    
    # Check environment variables
    required_vars = ['GROQ_API_KEY', 'OPENAI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_INDEX_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return
    
    print("✓ All required environment variables found")
    print()
    
    # Run tests
    test_suite = ComprehensiveTest()
    await test_suite.run_all_tests()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
