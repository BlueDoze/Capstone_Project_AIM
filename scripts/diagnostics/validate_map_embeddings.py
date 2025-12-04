#!/usr/bin/env python3
"""
Validation of Map Embeddings Quality
=====================================

This script validates the quality of embeddings generated for the Building M floor plan.
It tests common navigation queries and measures how well the embeddings can retrieve
the correct floor plan map.

Usage:
    python3 validate_map_embeddings.py
"""

import os
import sys
import pickle
import numpy as np

def load_image_metadata():
    """Load processed image metadata from cache"""
    cache_file = "image_metadata_cache.pkl"

    if not os.path.exists(cache_file):
        print(f"❌ Cache file not found: {cache_file}")
        print("   Run: python3 main.py (to process images)")
        return None

    try:
        with open(cache_file, 'rb') as f:
            df_imagens = pickle.load(f)
        print(f"✅ Loaded {len(df_imagens)} processed images from cache")
        return df_imagens
    except Exception as e:
        print(f"❌ Error loading cache: {e}")
        return False

def test_embedding_quality():
    """Test the quality of embeddings with realistic navigation queries"""

    print("\n" + "="*70)
    print("🧪 VALIDATION: BUILDING M FLOOR 1 - NAVIGATION EMBEDDINGS")
    print("="*70)

    # Load cache
    print("\n1️⃣  Loading image metadata...")
    df_imagens = load_image_metadata()
    if df_imagens is None or df_imagens.empty:
        return False

    # Import and initialize required functions
    try:
        print("\n2️⃣  Initializing embedding models...")
        from multimodal_rag_complete import (
            inicializar_modelos,
            get_text_embedding_from_text_embedding_model,
        )

        # Initialize models
        if not inicializar_modelos():
            print("❌ Failed to initialize models")
            return False
        print("✅ Models initialized")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error initializing models: {e}")
        return False

    # Test queries - realistic navigation requests in Building M
    test_queries = [
        # Room-to-room navigation
        "How do I get to Room 1003?",
        "Can you help me find Room 1018?",
        "Directions from Room 1003 to Room 1040",
        "How to reach Room 1049?",

        # Facility searches
        "Where is the bathroom?",
        "Where are the bathrooms in Building M?",
        "How do I find the elevator?",
        "Where are the stairs?",

        # Navigation descriptions
        "Show me the floor plan for Building M",
        "I need walking directions in Building M Floor 1",
        "Navigate to the exit",

        # Mixed queries
        "From bathroom to Room 1030",
        "How to go from the elevator to Room 1045",
    ]

    print(f"\n3️⃣  Testing {len(test_queries)} navigation queries...")
    print("="*70)

    # Store results for analysis
    results = []

    for query_idx, query in enumerate(test_queries, 1):
        print(f"\n📍 Query {query_idx}/{len(test_queries)}: '{query}'")

        try:
            # Generate embedding for the query
            query_embedding = np.array(get_text_embedding_from_text_embedding_model(query))

            # Calculate similarity with all images
            scores = []
            for img_idx, (idx, row) in enumerate(df_imagens.iterrows()):
                try:
                    # Use text embedding from description if available
                    if row['text_embedding_from_image_description']:
                        img_embedding = np.array(row['text_embedding_from_image_description'])
                        # Calculate cosine similarity manually
                        similarity = np.dot(query_embedding, img_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(img_embedding) + 1e-10
                        )
                        scores.append({
                            'idx': idx,
                            'filename': row['original_filename'],
                            'score': similarity
                        })
                except Exception as e:
                    print(f"      ⚠️  Error processing image {row['original_filename']}: {e}")
                    continue

            # Sort by score
            scores.sort(key=lambda x: x['score'], reverse=True)

            # Analyze top result
            if scores:
                top_result = scores[0]
                score = top_result['score']

                print(f"   Top match: {top_result['filename']}")
                print(f"   Similarity score: {score:.3f}")

                # Quality assessment
                if score > 0.7:
                    print("   ✅ EXCELLENT - Strong relevance")
                    quality = "excellent"
                elif score > 0.6:
                    print("   ✅ GOOD - Acceptable relevance")
                    quality = "good"
                elif score > 0.5:
                    print("   ⚠️  FAIR - Weak relevance")
                    quality = "fair"
                else:
                    print("   ❌ POOR - Very weak relevance")
                    quality = "poor"

                results.append({
                    'query': query,
                    'score': score,
                    'quality': quality,
                    'top_image': top_result['filename']
                })
            else:
                print("   ❌ No images found")
                results.append({
                    'query': query,
                    'score': 0,
                    'quality': 'error',
                    'top_image': 'N/A'
                })

        except Exception as e:
            print(f"   ❌ Error processing query: {e}")
            results.append({
                'query': query,
                'score': 0,
                'quality': 'error',
                'top_image': 'N/A'
            })

    # Generate summary report
    print("\n" + "="*70)
    print("📊 VALIDATION SUMMARY REPORT")
    print("="*70)

    if results:
        # Calculate statistics
        scores = [r['score'] for r in results if r['score'] > 0]
        if scores:
            avg_score = np.mean(scores)
            min_score = np.min(scores)
            max_score = np.max(scores)
        else:
            avg_score = min_score = max_score = 0

        # Count quality levels
        quality_counts = {}
        for r in results:
            q = r['quality']
            quality_counts[q] = quality_counts.get(q, 0) + 1

        print(f"\n📈 Statistics:")
        print(f"   - Average similarity score: {avg_score:.3f}")
        print(f"   - Minimum score: {min_score:.3f}")
        print(f"   - Maximum score: {max_score:.3f}")

        print(f"\n📊 Quality Distribution:")
        print(f"   - Excellent (>0.7): {quality_counts.get('excellent', 0)} queries")
        print(f"   - Good (0.6-0.7): {quality_counts.get('good', 0)} queries")
        print(f"   - Fair (0.5-0.6): {quality_counts.get('fair', 0)} queries")
        print(f"   - Poor (<0.5): {quality_counts.get('poor', 0)} queries")
        print(f"   - Errors: {quality_counts.get('error', 0)} queries")

        # Overall assessment
        excellent_ratio = quality_counts.get('excellent', 0) / len(results)
        good_ratio = (quality_counts.get('excellent', 0) + quality_counts.get('good', 0)) / len(results)

        print(f"\n🎯 Overall Assessment:")
        if good_ratio >= 0.8 and avg_score > 0.65:
            print("   ✅ EMBEDDINGS ARE HIGH QUALITY")
            print("   Ready for production use in navigation system")
            success = True
        elif good_ratio >= 0.6 and avg_score > 0.55:
            print("   ⚠️  EMBEDDINGS ARE ACCEPTABLE")
            print("   Usable but could be improved")
            success = True
        else:
            print("   ❌ EMBEDDINGS NEED IMPROVEMENT")
            print("   Consider refining descriptions or prompt")
            success = False

        print("\n" + "="*70)
        print("💡 Recommendations:")
        if success:
            print("   ✅ Embeddings quality is acceptable")
            print("   📌 Next: Deploy updated system and monitor real usage")
        else:
            print("   1. Check if new prompts were applied")
            print("   2. Verify image descriptions are detailed")
            print("   3. Review Gemini response for quality")
            print("   4. Consider refining the navigation prompt")

        print("="*70 + "\n")

        return success
    else:
        print("❌ No results to analyze")
        return False

if __name__ == "__main__":
    try:
        print("\n🚀 BUILDING M EMBEDDING VALIDATION")
        success = test_embedding_quality()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
