import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import MainLayout from './components/MainLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import EmployeeList from './pages/EmployeeList'
import EmployeeForm from './pages/EmployeeForm'
import EmployeeDetail from './pages/EmployeeDetail'
import AuditLogList from './pages/AuditLogList'

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="employees" element={<EmployeeList />} />
          <Route path="employees/new" element={<EmployeeForm />} />
          <Route path="employees/:id" element={<EmployeeDetail />} />
          <Route path="employees/:id/edit" element={<EmployeeForm />} />
          <Route path="audit-logs" element={<AuditLogList />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
