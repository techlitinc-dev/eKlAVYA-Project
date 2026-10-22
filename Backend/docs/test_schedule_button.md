# Testing Schedule Exam Button in Parent Dashboard

## What Was Added

### 1. Quick Access Card (Overview Tab)
- Location: Top of Overview tab, alongside "Complete Syllabus" and "Study Center"
- Features:
  - Green gradient card with Calendar icon
  - "Schedule Exam" title
  - "Book diagnostic test slot" description
  - Green "Schedule" button
  - Navigates to `/schedule-diagnostic` on click

### 2. Schedule Tab Section
- Location: Top of Schedule tab
- Features:
  - Prominent green card with scheduling information
  - Shows current test status (scheduled or not)
  - Dynamic button text: "Schedule Test" or "Reschedule Test"
  - Larger button size for visibility
  - Navigates to `/schedule-diagnostic` on click

## How to Test

### Manual Testing Steps:

1. **Start the development server:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Login as a parent:**
   - Navigate to http://localhost:3000/auth
   - Login with parent credentials

3. **Test Overview Tab:**
   - You should see the parent dashboard
   - Look for the green "Schedule Exam" card in the top row
   - Click the "Schedule" button
   - Should navigate to `/schedule-diagnostic` page

4. **Test Schedule Tab:**
   - Click on the "Schedule" tab
   - Look for the green "Schedule Diagnostic Test" card at the top
   - Click the "Schedule Test" button
   - Should navigate to `/schedule-diagnostic` page

5. **Verify Schedule Diagnostic Page:**
   - Page should load with a calendar interface
   - Should show exam information on the left
   - Should allow date and time selection
   - Should have a "Schedule Diagnostic Test" button

## Troubleshooting

### If button doesn't work:

1. **Check browser console for errors:**
   - Open DevTools (F12)
   - Look for JavaScript errors
   - Check Network tab for failed API calls

2. **Verify authentication:**
   - Make sure you're logged in as a parent (not student)
   - Check localStorage for 'token' and 'user' data

3. **Check routing:**
   - Verify `/schedule-diagnostic` page exists
   - Check if Next.js router is working properly

4. **Backend API:**
   - Ensure backend server is running on port 8000
   - Check if `/api/diagnostic-test/schedule` endpoint is accessible
   - Verify CORS settings allow frontend requests

### Common Issues:

1. **Button click does nothing:**
   - Check if onClick handler is properly bound
   - Verify router is imported and initialized
   - Look for JavaScript errors in console

2. **Page not found (404):**
   - Verify `frontend/src/app/schedule-diagnostic/page.tsx` exists
   - Restart Next.js dev server
   - Clear `.next` cache: `rm -rf .next`

3. **Authentication redirect:**
   - If redirected to `/auth`, verify parent credentials
   - Check if user role is correctly set
   - Verify JWT token is valid

## Code Changes Made

### File: `frontend/src/app/parent-dashboard/page.tsx`

1. **Changed grid layout from 2 to 3 columns:**
   ```tsx
   <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
   ```

2. **Added Schedule Exam card:**
   ```tsx
   <Card className="border-2 border-green-200 bg-gradient-to-r from-green-50 to-emerald-50">
     <CardContent className="p-6">
       <div className="flex items-center justify-between">
         <div className="flex items-center gap-4">
           <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
             <Calendar className="w-6 h-6 text-green-600" />
           </div>
           <div>
             <h3 className="text-lg font-bold text-gray-900">Schedule Exam</h3>
             <p className="text-sm text-gray-600">Book diagnostic test slot</p>
           </div>
         </div>
         <Button onClick={() => router.push('/schedule-diagnostic')} className="bg-green-600 hover:bg-green-700">
           Schedule
         </Button>
       </div>
     </CardContent>
   </Card>
   ```

3. **Added Schedule tab section:**
   ```tsx
   <Card className="border-2 border-green-200 bg-gradient-to-r from-green-50 to-emerald-50">
     <CardHeader>
       <CardTitle className="flex items-center gap-2">
         <Calendar className="w-5 h-5 text-green-600" />
         Schedule Diagnostic Test
       </CardTitle>
       <CardDescription>Book a time slot for your child's diagnostic exam</CardDescription>
     </CardHeader>
     <CardContent>
       <div className="flex items-center justify-between">
         <div className="flex-1">
           <p className="text-sm text-gray-700 mb-2">
             Schedule a diagnostic test to assess your child's current level and identify areas for improvement.
           </p>
           <p className="text-xs text-gray-600">
             {diagnosticTest?.status === 'scheduled' 
               ? `Test scheduled for ${new Date(diagnosticTest.scheduled_date).toLocaleString()}`
               : 'No test scheduled yet'}
           </p>
         </div>
         <Button 
           onClick={() => router.push('/schedule-diagnostic')} 
           className="bg-green-600 hover:bg-green-700 ml-4"
           size="lg"
         >
           <Calendar className="mr-2 h-5 w-5" />
           {diagnosticTest?.status === 'scheduled' ? 'Reschedule Test' : 'Schedule Test'}
         </Button>
       </div>
     </CardContent>
   </Card>
   ```

### File: `frontend/src/app/onboarding/child-profile/page.tsx`

- Added missing `examAPI` import to fix build error

## Backend Endpoint

The schedule functionality uses this endpoint:
- **POST** `/api/diagnostic-test/schedule`
- Request body:
  ```json
  {
    "child_id": "string",
    "exam_type": "string",
    "scheduled_date": "ISO 8601 datetime string",
    "test_id": "string"
  }
  ```
- Response:
  ```json
  {
    "test_id": "string",
    "scheduled_date": "string",
    "status": "scheduled",
    "message": "Diagnostic test scheduled successfully"
  }
  ```

## Status

✅ Code changes implemented
✅ Build successful
✅ No TypeScript errors
✅ Backend endpoint exists
✅ Routing configured correctly

The schedule exam functionality is now fully integrated into the parent dashboard!
