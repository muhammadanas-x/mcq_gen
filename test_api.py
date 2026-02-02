"""
Test script for MCQ Generator API

Simple script to test the API endpoints.
"""

import requests
import json
import time
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Health check failed"
    print("✓ Health check passed")


def test_generate_mcqs(test_file_path: str, subject: str = "Test Subject - Calculus"):
    """Test MCQ generation endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Generate MCQs")
    print("="*60)
    
    if not Path(test_file_path).exists():
        print(f"⚠ Test file not found: {test_file_path}")
        print("Skipping generation test")
        return None
    
    print(f"Uploading file: {test_file_path}")
    print(f"Subject: {subject}")
    
    with open(test_file_path, "rb") as f:
        files = {"file": (Path(test_file_path).name, f, "text/markdown")}
        data = {
            "subject": subject,
            "input_type": "chapter",
            "include_explanations": True
        }
        
        print("Sending request (this may take 2-5 minutes)...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/generate-mcqs",
            files=files,
            data=data
        )
        
        elapsed = time.time() - start_time
    
    print(f"Status Code: {response.status_code}")
    print(f"Time Elapsed: {elapsed:.2f} seconds")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Generation successful!")
        print(f"  Session ID: {result['session_id']}")
        print(f"  MCQs Generated: {result['total_mcqs_generated']}")
        print(f"  Difficulty Distribution: {result['difficulty_distribution']}")
        print(f"\n  First MCQ:")
        if result['mcqs']:
            first_mcq = result['mcqs'][0]
            print(f"    Q{first_mcq['question_number']}: {first_mcq['stem'][:60]}...")
            print(f"    Correct Answer: ({first_mcq['correct_answer']})")
        
        return result['session_id']
    else:
        print(f"✗ Generation failed!")
        print(f"Error: {response.text}")
        return None


def test_list_sessions():
    """Test list sessions endpoint"""
    print("\n" + "="*60)
    print("TEST 3: List Sessions")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/sessions?limit=5")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Found {result['total']} total sessions")
        print(f"  Showing {len(result['sessions'])} sessions:")
        
        for session in result['sessions']:
            print(f"\n  Session: {session['session_id'][:20]}...")
            print(f"    File: {session['input_filename']}")
            print(f"    MCQs: {session['total_mcqs_generated']}")
            print(f"    Status: {session['status']}")
    else:
        print(f"✗ Failed to list sessions")
        print(f"Error: {response.text}")


def test_get_session(session_id: str):
    """Test get session details endpoint"""
    print("\n" + "="*60)
    print("TEST 4: Get Session Details")
    print("="*60)
    
    if not session_id:
        print("⚠ No session ID provided, skipping")
        return
    
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        session = response.json()
        print(f"\n✓ Session Details:")
        print(f"  Session ID: {session['session_id']}")
        print(f"  Input: {session['input_filename']} ({session['input_type']})")
        print(f"  LLM: {session['llm_provider']} - {session['model']}")
        print(f"  Concepts Extracted: {session['total_concepts_extracted']}")
        print(f"  MCQs Generated: {session['total_mcqs_generated']}")
        print(f"  Difficulty: {session['difficulty_distribution']}")
        print(f"  Status: {session['status']}")
    else:
        print(f"✗ Failed to get session")
        print(f"Error: {response.text}")


def test_list_subjects():
    """Test list subjects endpoint"""
    print("\n" + "="*60)
    print("TEST 4: List Subjects")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/subjects")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Found {result['total_subjects']} unique subjects:")
        
        for subject_stat in result['subjects']:
            print(f"\n  Subject: {subject_stat['subject']}")
            print(f"    Sessions: {subject_stat['total_sessions']}")
            print(f"    MCQs: {subject_stat['total_mcqs']}")
    else:
        print(f"✗ Failed to list subjects")
        print(f"Error: {response.text}")


def test_list_mcqs(session_id: str = None, subject: str = None):
    """Test list MCQs endpoint"""
    print("\n" + "="*60)
    print("TEST 5: List MCQs")
    print("="*60)
    
    url = f"{BASE_URL}/mcqs?limit=3"
    if session_id:
        url += f"&session_id={session_id}"
        print(f"Filtering by session: {session_id[:20]}...")
    if subject:
        url += f"&subject={subject}"
        print(f"Filtering by subject: {subject}")
    
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Found {result['total']} total MCQs")
        print(f"  Showing {len(result['mcqs'])} MCQs:")
        
        for mcq in result['mcqs']:
            print(f"\n  Q{mcq['question_number']}: {mcq['stem'][:60]}...")
            print(f"    Subject: {mcq['subject']}")
            print(f"    Options: {list(mcq['options'].keys())}")
            print(f"    Correct: ({mcq['correct_answer']}) {mcq['options'][mcq['correct_answer']][:40]}...")
            print(f"    Difficulty: {mcq['metadata']['difficulty']}")
    else:
        print(f"✗ Failed to list MCQs")
        print(f"Error: {response.text}")


def test_get_mcq(mcq_id: str):
    """Test get MCQ details endpoint"""
    print("\n" + "="*60)
    print("TEST 6: Get MCQ Details")
    print("="*60)
    
    if not mcq_id:
        print("⚠ No MCQ ID provided, skipping")
        return
    
    response = requests.get(f"{BASE_URL}/mcqs/{mcq_id}")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        mcq = response.json()
        print(f"\n✓ MCQ Details:")
        print(f"  ID: {mcq['id']}")
        print(f"  Question: {mcq['stem']}")
        print(f"\n  Options:")
        for key, value in mcq['options'].items():
            marker = " ← CORRECT" if key == mcq['correct_answer'] else ""
            print(f"    ({key}) {value}{marker}")
        print(f"\n  Explanations:")
        for key, value in mcq['explanation'].items():
            print(f"    ({key}): {value[:80]}...")
    else:
        print(f"✗ Failed to get MCQ")
        print(f"Error: {response.text}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MCQ GENERATOR API - TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print("="*60)
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2: Generate MCQs (optional - requires input file)
        # Modify this path to your test file
        test_file = "../chapter3.md"  # or use a small sample file
        test_subject = "Calculus - Integration"
        
        session_id = None
        if Path(test_file).exists():
            session_id = test_generate_mcqs(test_file, subject=test_subject)
        else:
            print(f"\n⚠ Test file not found: {test_file}")
            print("Skipping generation test. You can:")
            print("  1. Create a sample markdown file")
            print("  2. Use the API manually to generate MCQs")
            print("  3. Continue with read-only tests below")
        
        # Test 3: List sessions
        test_list_sessions()
        
        # Test 4: List subjects
        test_list_subjects()
        
        # Test 4: Get session details
        if session_id:
            test_get_session(session_id)
        
        # Test 5: List MCQs
        test_list_mcqs(session_id)
        
        # Test 6: Get MCQ details (requires MCQ ID from previous test)
        # You can manually set an MCQ ID here if you have one
        
        print("\n" + "="*60)
        print("✓ TEST SUITE COMPLETED")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to API server")
        print("Make sure the server is running:")
        print("  python server.py")
        print("="*60)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        print("="*60)


if __name__ == "__main__":
    main()
