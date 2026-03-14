"""Vector store for course recommendations using ChromaDB"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import pandas as pd
from pathlib import Path
from langchain_openai import OpenAIEmbeddings


class CourseVectorStore:
    """Manages course data in ChromaDB with OpenAI embeddings"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB vector store for courses
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings()
        
        # Get or create collection
        self.collection_name = "courses"
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except:
            self.collection = self.client.create_collection(name=self.collection_name)
    
    def load_courses_from_excel(self, excel_path: str) -> int:
        """
        Load courses from Excel file into vector store
        
        Args:
            excel_path: Path to the Course Master List Excel file
            
        Returns:
            Number of courses loaded
        """
        try:
            # Read Excel file
            df = pd.read_excel(excel_path)
            
            # Expected columns: Course ID, Course Name, Summary
            required_columns = ['Course ID', 'Course Full Name', 'summary']
            
            # Check if all required columns exist
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Required column '{col}' not found in Excel file")
            
            # Prepare data for ingestion
            documents = []
            metadatas = []
            ids = []
            
            for _, row in df.iterrows():
                course_id = str(row['Course ID'])
                course_name = str(row['Course Full Name'])
                summary = str(row['summary'])
                
                # Create searchable text combining name and summary
                searchable_text = f"{course_name}\n{summary}"
                
                documents.append(searchable_text)
                metadatas.append({
                    'course_id': course_id,
                    'course_name': course_name,
                    'summary': summary
                })
                ids.append(course_id)
            
            # Generate embeddings and add in batches to avoid size limits
            batch_size = 5000  # Safe batch size below ChromaDB limit
            total_courses = len(documents)
            
            for i in range(0, total_courses, batch_size):
                batch_end = min(i + batch_size, total_courses)
                batch_documents = documents[i:batch_end]
                batch_metadatas = metadatas[i:batch_end]
                batch_ids = ids[i:batch_end]
                
                # Generate embeddings for this batch
                batch_embeddings = self.embeddings.embed_documents(batch_documents)
                
                # Add batch to ChromaDB collection
                self.collection.add(
                    documents=batch_documents,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
            
            return total_courses
            
        except Exception as e:
            raise Exception(f"Failed to load courses from Excel: {str(e)}")
    
    def search_courses(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for relevant courses based on query
        
        Args:
            query: Search query (skills, topics, etc.)
            n_results: Number of results to return
            
        Returns:
            List of relevant courses with metadata
        """
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            courses = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    course = {
                        'course_id': results['metadatas'][0][i]['course_id'],
                        'course_name': results['metadatas'][0][i]['course_name'],
                        'summary': results['metadatas'][0][i]['summary'],
                        'distance': results['distances'][0][i] if 'distances' in results else 0
                    }
                    courses.append(course)
            
            return courses
            
        except Exception as e:
            raise Exception(f"Failed to search courses: {str(e)}")
    
    def search_courses_for_skills(self, skills: List[str], n_results_per_skill: int = 3) -> Dict[str, List[Dict]]:
        """
        Search for courses relevant to multiple skills
        
        Args:
            skills: List of skill names
            n_results_per_skill: Number of course results per skill
            
        Returns:
            Dictionary mapping skills to relevant courses
        """
        skill_courses = {}
        
        for skill in skills:
            courses = self.search_courses(skill, n_results=n_results_per_skill)
            skill_courses[skill] = courses
        
        return skill_courses
    
    def get_course_by_id(self, course_id: str) -> Optional[Dict]:
        """
        Get course details by ID
        
        Args:
            course_id: Course ID
            
        Returns:
            Course details or None if not found
        """
        try:
            results = self.collection.get(
                ids=[course_id]
            )
            
            if results['documents'] and len(results['documents']) > 0:
                return {
                    'course_id': results['metadatas'][0]['course_id'],
                    'course_name': results['metadatas'][0]['course_name'],
                    'summary': results['metadatas'][0]['summary']
                }
            
            return None
            
        except Exception as e:
            return None
    
    def clear_collection(self):
        """Clear all courses from the collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(name=self.collection_name)
        except Exception as e:
            raise Exception(f"Failed to clear collection: {str(e)}")
    
    def get_course_count(self) -> int:
        """Get total number of courses in the collection"""
        try:
            return self.collection.count()
        except:
            return 0
