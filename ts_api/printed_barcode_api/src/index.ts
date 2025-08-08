import { Hono } from 'hono'
import { createClient } from '@supabase/supabase-js'
import { Database } from './database.types'

const SUPABASE_USER_PASSWORD = process.env.SUPABASE_USER_PASSWORD!
const SUPABASE_API_KEY = process.env.SUPABASE_API_KEY!
const SUPABASE_URL = process.env.SUPABASE_URL!
const SUPABASE_USER_EMAIL = process.env.SUPABASE_USER_EMAIL!
const BARCODE_API_KEY = process.env.BARCODE_API_KEY!

const app = new Hono()

// Simple in-memory rate limiting for local use
const requestCounts = new Map<string, { count: number; resetTime: number }>()
const RATE_LIMIT_WINDOW = 60 * 1000
const MAX_REQUESTS_PER_WINDOW = 10

function checkRateLimit(ip: string): boolean {
  const now = Date.now()
  const record = requestCounts.get(ip)
  
  if (!record || now > record.resetTime) {
    requestCounts.set(ip, { count: 1, resetTime: now + RATE_LIMIT_WINDOW })
    return true
  }
  
  if (record.count >= MAX_REQUESTS_PER_WINDOW) {
    return false
  }
  
  record.count++
  return true
}

let supabase: ReturnType<typeof createClient<Database>>

// Try authing at startup maybe this will time out eventually?
// will refactor if this is the case
async function initializeApp() {
  try {
    // Validate environment variables
    if (!SUPABASE_URL || !SUPABASE_API_KEY || !SUPABASE_USER_EMAIL || !SUPABASE_USER_PASSWORD || !BARCODE_API_KEY) {
      throw new Error('Missing required environment variables')
    }
    
    supabase = createClient<Database>(SUPABASE_URL, SUPABASE_API_KEY)
    
    const { data, error } = await supabase.auth.signInWithPassword({
      email: SUPABASE_USER_EMAIL,
      password: SUPABASE_USER_PASSWORD,
    })
    
    if (error) {
      console.error('Authentication error:', error)
      throw new Error('Failed to authenticate with Supabase')
    }
    
    console.log('Successfully authenticated with Supabase')
    return data.user
  } catch (error) {
    console.error('Failed to authenticate:', error)
    process.exit(1)
  }
}

app.use('*', (c, next) => {
  const method = c.req.method
  const url = c.req.url
  const userAgent = c.req.header('user-agent') || 'unknown'
  const clientIP = c.req.header('x-forwarded-for') || c.req.header('x-real-ip') || 'unknown'
  
  console.log(`[${new Date().toISOString()}] ${method} ${url} - IP: ${clientIP} - UA: ${userAgent}`)
  
  return next()
})

app.get('/', (c) => {
  return c.text('yo the barcode API is running :-)')
})

app.get('/barcode/:api_key/:task_barcode_id', async (c) => {
  // DOes this rate limiting work IDK bro
  const clientIP = c.req.header('x-forwarded-for') || c.req.header('x-real-ip') || 'unknown'
  if (!checkRateLimit(clientIP)) {
    console.log(`Rate limit exceeded for ${clientIP}`)
    return c.text('Too many requests', 429)
  }

  const providedKey = c.req.param('api_key')
  const taskBarcodeIdParam = c.req.param('task_barcode_id')

  if (!providedKey || providedKey !== BARCODE_API_KEY) {
    return c.text('Invalid API key', 401)
  }

  const taskBarcodeId = parseInt(taskBarcodeIdParam)
  if (isNaN(taskBarcodeId) || taskBarcodeId <= 0) {
    return c.text('Invalid task barcode ID', 400)
  }

  try {
    // Check if task exists first since we do not know
    // how consistent the barcode scanning is going to be
    // remove later if the barcode scanning is good enuff
    // because if a barcode scans the task exists (probably idk)
    const { data: existingTask, error: fetchError } = await supabase
        .from('tasks')
        .select('*')
        .eq('task_barcode_id', taskBarcodeId)
        .single()

    if (fetchError) {
      return c.text(`Error fetching task: ${fetchError.message}`, 500)
    }

    if (!existingTask) {
      const attemptedUrl = c.req.url
      console.log(`Task not found for barcode ID ${taskBarcodeId} - URL: ${attemptedUrl}`)
      return c.text(`Task not found for barcode ID: ${taskBarcodeId}. Attempted URL: ${attemptedUrl}`, 404)
    }

    const { error: updateError } = await supabase
        .from('tasks')
        .update({
          task_completed: true,
          task_completed_on: new Date().toISOString()
        })
        .eq('task_barcode_id', taskBarcodeId)

    if (updateError) {
      return c.text(`Error updating task: ${updateError.message}`, 500)
    }

    return c.json({ success: true, message: 'Task marked as completed! GOOD JOB!!! :-D' })
  } catch (error) {
    console.error('Error:', error)
    return c.text('Internal server error', 500)
  }
})

// Catch-all route for unmatched URLs
app.all('*', (c) => {
  const method = c.req.method
  const url = c.req.url
  const message = `404 Not Found - ${method} ${url}
  
Available endpoints:
- GET / (API status)
- GET /barcode/<api_key>/<task_barcode_id> (mark task complete)

Your URL: ${url}
Expected format: /barcode/YOUR_API_KEY/BARCODE_ID

Example: /barcode/mykey123/42`

  console.log(`404 - Unmatched route: ${method} ${url}`)
  return c.text(message, 404)
})

initializeApp()

export default app
