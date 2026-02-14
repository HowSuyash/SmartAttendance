    def get_institution_analytics(self, institution_id: str, days: int = 30) -> Dict:
        """
        Get comprehensive analytics for an institution.
        
        Args:
            institution_id: Institution ID
            days: Number of days to analyze
            
        Returns:
            Analytics data with overall stats and trends
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all sessions for this institution
            sessions_ref = self.db.collection('sessions')\
                .where('institution_id', '==', institution_id)\
                .where('timestamp', '>=', cutoff_date)\
                .where('status', '==', 'completed')\
                .stream()
            
            sessions = []
            total_students = 0
            total_engaged = 0
            total_disengaged = 0
            classes_map = {}
            
            for doc in sessions_ref:
                session = doc.to_dict()
                session['id'] = doc.id
                sessions.append(session)
                
                stats = session.get('statistics', {})
                total_students += stats.get('total_faces', 0)
                total_engaged += stats.get('engaged_count', 0)
                total_disengaged += stats.get('disengaged_count', 0)
                
                # Track per-class data
                class_name = session.get('class_name', 'Unknown')
                if class_name not in classes_map:
                    classes_map[class_name] = {
                        'total_sessions': 0,
                        'total_students': 0,
                        'total_engaged': 0,
                        'avg_engagement': 0
                    }
                
                classes_map[class_name]['total_sessions'] += 1
                classes_map[class_name]['total_students'] += stats.get('total_faces', 0)
                classes_map[class_name]['total_engaged'] += stats.get('engaged_count', 0)
            
            # Calculate class averages
            for class_name in classes_map:
                class_data = classes_map[class_name]
                if class_data['total_students'] > 0:
                    class_data['avg_engagement'] = (class_data['total_engaged'] / class_data['total_students']) * 100
            
            # Calculate overall metrics
            total_sessions = len(sessions)
            avg_engagement = (total_engaged / total_students * 100) if total_students > 0 else 0
            
            return {
                'total_sessions': total_sessions,
                'total_students': total_students,
                'total_engaged': total_engaged,
                'total_disengaged': total_disengaged,
                'avg_engagement_percentage': round(avg_engagement, 2),
                'classes': classes_map,
                'recent_sessions': sessions[:10]  # Last 10 sessions
            }
            
        except Exception as e:
            print(f"Error getting institution analytics: {e}")
            return {}
    
    def get_student_attendance(self, student_id: str) -> Dict:
        """
        Get attendance records and statistics for a student.
        
        Args:
            student_id: Student ID
            
        Returns:
            Student attendance data
        """
        try:
            # Get student info
            student_doc = self.db.collection('students').document(student_id).get()
            if not student_doc.exists:
                return {}
            
            student_data = student_doc.to_dict()
            institution_id = student_data.get('institution_id')
            
            # Get all attendance records for this student
            attendance_ref = self.db.collection('attendance_records')\
                .where('student_id', '==', student_id)\
                .order_by('date', direction=firestore.Query.DESCENDING)\
                .stream()
            
            records = []
            total_classes = 0
            present_count = 0
            engaged_count = 0
            
            for doc in attendance_ref:
                record = doc.to_dict()
                record['id'] = doc.id
                records.append(record)
                
                total_classes += 1
                if record.get('was_present'):
                    present_count += 1
                if record.get('engagement') == 'engaged':
                    engaged_count += 1
            
            # Calculate percentages
            attendance_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0
            engagement_percentage = (engaged_count / present_count * 100) if present_count > 0 else 0
            
            return {
                'student_id': student_id,
                'student_name': student_data.get('student_name'),
                'student_number': student_data.get('student_number'),
                'total_classes': total_classes,
                'present_count': present_count,
                'attendance_percentage': round(attendance_percentage, 2),
                'engagement_percentage': round(engagement_percentage, 2),
                'records': records
            }
            
        except Exception as e:
            print(f"Error getting student attendance: {e}")
            return {}
    
    def create_attendance_record(self, student_id: str, session_id: str, was_present: bool, engagement: str) -> str:
        """
        Create an attendance record for a student.
        
        Args:
            student_id: Student ID
            session_id: Session ID
            was_present: Whether student was present
            engagement: Engagement level (engaged/disengaged/unknown)
            
        Returns:
            Record ID
        """
        try:
            # Get session info
            session = self.db.collection('sessions').document(session_id).get()
            if not session.exists:
                return None
            
            session_data = session.to_dict()
            
            # Create attendance record
            record_data = {
                'student_id': student_id,
                'session_id': session_id,
                'class_name': session_data.get('class_name'),
                'date': session_data.get('timestamp'),
                'was_present': was_present,
                'engagement': engagement,
                'created_at': datetime.utcnow()
            }
            
            doc_ref = self.db.collection('attendance_records').add(record_data)
            return doc_ref[1].id
            
        except Exception as e:
            print(f"Error creating attendance record: {e}")
            return None
