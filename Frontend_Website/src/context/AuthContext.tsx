import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../lib/api';

export type UserRole = 'student' | 'parent' | 'superadmin';

export interface UserSession {
  token: string;
  role: UserRole;
  name: string;
  email?: string;
  username?: string;
  userId?: string;
  studentId?: string;
  examType?: string;
  student_id?: string;
  child_id?: string;
  parent_id?: string;
  target_exam?: string;
}

interface AuthContextType {
  user: UserSession | null;
  session: UserSession | null;
  loading: boolean;
  selectedExam: 'jee_main' | 'jee_advanced' | 'neet';
  setSelectedExam: (exam: 'jee_main' | 'jee_advanced' | 'neet') => void;
  loginWithSession: (session: UserSession) => void;
  switchDemoRole: (role: UserRole) => Promise<UserSession>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const normalizeSession = (raw: UserSession, selectedExam: string): UserSession => ({
  ...raw,
  userId: raw.userId || raw.parent_id || raw.student_id || raw.child_id || 'child_demo_aarav',
  studentId: raw.studentId || raw.student_id || raw.child_id || 'child_demo_aarav',
  examType: (raw.examType || raw.target_exam || selectedExam || 'JEE_MAIN').toUpperCase(),
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserSession | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedExam, setSelectedExamState] = useState<'jee_main' | 'jee_advanced' | 'neet'>(
    () => (localStorage.getItem('eklavya_exam') as any) || 'jee_main'
  );

  const setSelectedExam = (exam: 'jee_main' | 'jee_advanced' | 'neet') => {
    setSelectedExamState(exam);
    localStorage.setItem('eklavya_exam', exam);
    setUser((prev) => (prev ? normalizeSession(prev, exam) : prev));
  };

  const loginWithSession = (sessionData: UserSession) => {
    const norm = normalizeSession(sessionData, selectedExam);
    setUser(norm);
    localStorage.setItem('eklavya_token', norm.token);
    localStorage.setItem('eklavya_user', JSON.stringify(norm));
  };

  const switchDemoRole = async (role: UserRole): Promise<UserSession> => {
    const res = await api.post('/api/superadmin/demo-session', { role });
    const active: UserSession = normalizeSession(res.data.active_session, selectedExam);
    loginWithSession(active);
    if (res.data.all_sessions) {
      localStorage.setItem('eklavya_all_demo_sessions', JSON.stringify(res.data.all_sessions));
    }
    return active;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('eklavya_token');
    localStorage.removeItem('eklavya_user');
  };

  useEffect(() => {
    const init = async () => {
      const saved = localStorage.getItem('eklavya_user');
      if (saved) {
        try {
          const parsed = normalizeSession(JSON.parse(saved) as UserSession, selectedExam);
          setUser(parsed);
          setLoading(false);
          return;
        } catch {
          // fallback to demo seed
        }
      }
      try {
        await switchDemoRole('student');
      } catch {
        // backend might still be starting
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        session: user,
        loading,
        selectedExam,
        setSelectedExam,
        loginWithSession,
        switchDemoRole,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
