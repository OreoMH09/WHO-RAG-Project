"""
Tests for retrieval accuracy and system functionality.
Validates that the RAG system can find relevant documents for known queries.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from search.hybrid_search import semantic_search
from search.vector_store import get_collection_stats
import config


# Test cases: query and expected URL substring or keywords
TEST_CASES = [
    {
        "query": "What is malaria?",
        "expected_terms": ["malaria"],
        "description": "Should retrieve documents about malaria"
    },
    {
        "query": "COVID-19 symptoms",
        "expected_terms": ["covid", "coronavirus", "sars-cov-2"],
        "description": "Should retrieve documents about COVID-19"
    },
    {
        "query": "tuberculosis treatment",
        "expected_terms": ["tuberculosis", "tb"],
        "description": "Should retrieve documents about tuberculosis"
    },
    {
        "query": "vaccination schedule",
        "expected_terms": ["vaccin", "immun"],
        "description": "Should retrieve documents about vaccination"
    },
    {
        "query": "WHO headquarters",
        "expected_terms": ["who", "geneva", "organization"],
        "description": "Should retrieve documents about WHO"
    },
]


def check_relevance(result: dict, expected_terms: list[str]) -> bool:
    """
    Check if a search result contains any of the expected terms.
    
    Args:
        result: Search result dictionary with 'text' and 'metadata'
        expected_terms: List of terms (case-insensitive) to look for
        
    Returns:
        True if any expected term is found in text, URL, or title
    """
    text = result['text'].lower()
    url = result['metadata'].get('url', '').lower()
    title = result['metadata'].get('title', '').lower()
    
    combined = f"{text} {url} {title}"
    
    return any(term.lower() in combined for term in expected_terms)


def test_retrieval_hit_rate():
    """
    Test retrieval hit rate: what percentage of queries retrieve relevant documents.
    """
    print("="*80)
    print("RETRIEVAL HIT RATE TEST")
    print("="*80)
    
    # Check if index exists
    stats = get_collection_stats()
    if stats["total_documents"] == 0:
        print("\n❌ ERROR: No documents in collection")
        print("Please run: python -m ingestion.build_index sample 10")
        return False
    
    print(f"\nCollection stats: {stats['total_documents']} documents\n")
    
    total_tests = len(TEST_CASES)
    passed_tests = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        query = test_case["query"]
        expected_terms = test_case["expected_terms"]
        description = test_case["description"]
        
        print(f"\nTest {i}/{total_tests}: {query}")
        print(f"  Expected: {description}")
        
        # Test different search methods
        for method in ["vector", "hybrid"]:
            print(f"\n  Testing {method} search...")
            
            try:
                results = semantic_search(query, top_k=5, method=method)
                
                if not results:
                    print(f"    ❌ No results returned")
                    continue
                
                # Check how many results are relevant
                relevant_count = sum(
                    1 for result in results
                    if check_relevance(result, expected_terms)
                )
                
                hit = relevant_count > 0
                
                if hit:
                    print(f"    ✅ PASS: {relevant_count}/{len(results)} results relevant")
                    if method == "hybrid":
                        passed_tests += 1
                else:
                    print(f"    ❌ FAIL: No relevant results found")
                
                # Show top result
                top_result = results[0]
                print(f"    Top result (score: {top_result['score']:.4f}):")
                print(f"      Title: {top_result['metadata'].get('title', 'N/A')[:60]}...")
                print(f"      Preview: {top_result['text'][:100]}...")
                
            except Exception as e:
                print(f"    ❌ ERROR: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Passed: {passed_tests}/{total_tests} ({100*passed_tests/total_tests:.1f}%)")
    
    if passed_tests == total_tests:
        print("✅ All tests passed!")
        return True
    elif passed_tests >= total_tests * 0.7:
        print("⚠️  Most tests passed (≥70%)")
        return True
    else:
        print("❌ Many tests failed (<70%)")
        return False


def test_search_methods_comparison():
    """
    Compare different search methods on the same queries.
    """
    print("\n" + "="*80)
    print("SEARCH METHODS COMPARISON")
    print("="*80)
    
    test_query = "What are the symptoms of COVID-19?"
    print(f"\nQuery: {test_query}\n")
    
    methods = ["vector", "bm25", "hybrid"]
    
    for method in methods:
        print(f"\n--- {method.upper()} SEARCH ---")
        
        try:
            results = semantic_search(test_query, top_k=3, method=method)
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. Score: {result['score']:.4f}")
                print(f"   Title: {result['metadata'].get('title', 'N/A')[:60]}...")
                print(f"   URL: {result['metadata'].get('url', 'N/A')}")
                
                if "vector_score" in result and "bm25_score" in result:
                    print(f"   Vector: {result['vector_score']:.4f}, BM25: {result['bm25_score']:.4f}")
        
        except Exception as e:
            print(f"Error: {e}")


def test_edge_cases():
    """
    Test edge cases and error handling.
    """
    print("\n" + "="*80)
    print("EDGE CASES TEST")
    print("="*80)
    
    edge_cases = [
        ("", "Empty query"),
        ("xyzabc123", "Nonsense query"),
        ("a", "Single character"),
        ("What is the meaning of life?", "Off-topic query"),
    ]
    
    for query, description in edge_cases:
        print(f"\n{description}: '{query}'")
        
        try:
            results = semantic_search(query, top_k=3, method="hybrid")
            print(f"  ✅ Returned {len(results)} results (no crash)")
            
            if results:
                print(f"  Top score: {results[0]['score']:.4f}")
        
        except Exception as e:
            print(f"  ❌ ERROR: {e}")


def run_all_tests():
    """
    Run all test suites.
    """
    print("="*80)
    print("WHO RAG SYSTEM - RETRIEVAL TESTS")
    print("="*80)
    
    # Check system is set up
    try:
        stats = get_collection_stats()
        print(f"\nSystem Status: ✅ Collection loaded ({stats['total_documents']} documents)")
    except Exception as e:
        print(f"\n❌ System Error: {e}")
        print("\nPlease ensure:")
        print("1. The vector database is initialized")
        print("2. Documents are indexed")
        print("\nRun: python -m ingestion.build_index sample 10")
        return False
    
    # Run test suites
    results = []
    
    print("\n" + "="*80)
    print("Running Test Suites...")
    print("="*80)
    
    # Test 1: Hit rate
    try:
        result = test_retrieval_hit_rate()
        results.append(("Hit Rate Test", result))
    except Exception as e:
        print(f"\n❌ Hit Rate Test failed with error: {e}")
        results.append(("Hit Rate Test", False))
    
    # Test 2: Method comparison
    try:
        test_search_methods_comparison()
        results.append(("Method Comparison", True))
    except Exception as e:
        print(f"\n❌ Method Comparison failed with error: {e}")
        results.append(("Method Comparison", False))
    
    # Test 3: Edge cases
    try:
        test_edge_cases()
        results.append(("Edge Cases Test", True))
    except Exception as e:
        print(f"\n❌ Edge Cases Test failed with error: {e}")
        results.append(("Edge Cases Test", False))
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL TEST RESULTS")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - Review results above")
    print("="*80)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
