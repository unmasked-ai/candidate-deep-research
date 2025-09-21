const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'

export interface WebSocketMessage {
  type: 'stage_update' | 'progress_update' | 'completion' | 'error' | 'agent_status'
  researchId: string
  data: {
    stage?: string
    status?: string
    progress?: number
    message?: string
    error?: string
    errorType?: string
    retryable?: boolean
    results?: any
    agent?: string
    currentTask?: string
    details?: Record<string, any>
  }
  timestamp: string
}

export interface WebSocketManager {
  connect(researchId: string): void
  disconnect(): void
  onMessage(callback: (message: WebSocketMessage) => void): void
  onError(callback: (error: Event) => void): void
  onClose(callback: (event: CloseEvent) => void): void
  onOpen(callback: () => void): void
  isConnected(): boolean
}

export class ResearchWebSocket implements WebSocketManager {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 1000
  private currentResearchId = ''
  private isManuallyDisconnected = false

  // Event callbacks
  private messageCallback?: (message: WebSocketMessage) => void
  private errorCallback?: (error: Event) => void
  private closeCallback?: (event: CloseEvent) => void
  private openCallback?: () => void

  connect(researchId: string): void {
    this.currentResearchId = researchId
    this.isManuallyDisconnected = false

    // Close existing connection if any
    if (this.ws) {
      this.ws.close()
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${WS_BASE_URL.replace(/^ws(s)?:/, protocol)}/ws/research/${researchId}`

    try {
      this.ws = new WebSocket(wsUrl)
      this.setupEventHandlers()
    } catch (error) {
      console.error('WebSocket connection failed:', error)
      this.errorCallback?.(error as Event)
    }
  }

  private setupEventHandlers(): void {
    if (!this.ws) return

    this.ws.onopen = () => {
      console.log('WebSocket connected for research:', this.currentResearchId)
      this.reconnectAttempts = 0
      this.openCallback?.()
    }

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)

        // Validate message structure
        if (message.type && message.researchId && message.data) {
          this.messageCallback?.(message)
        } else {
          console.warn('Invalid WebSocket message format:', message)
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error, event.data)
      }
    }

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)

      // Only attempt reconnection if not manually disconnected and connection was not clean
      if (!this.isManuallyDisconnected && !event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts)
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`)

        setTimeout(() => {
          this.reconnectAttempts++
          this.connect(this.currentResearchId)
        }, delay)
      } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached')
      }

      this.closeCallback?.(event)
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.errorCallback?.(error)
    }
  }

  disconnect(): void {
    this.isManuallyDisconnected = true
    this.reconnectAttempts = this.maxReconnectAttempts // Prevent reconnection

    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect')
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  // Event listener registration
  onMessage(callback: (message: WebSocketMessage) => void): void {
    this.messageCallback = callback
  }

  onError(callback: (error: Event) => void): void {
    this.errorCallback = callback
  }

  onClose(callback: (event: CloseEvent) => void): void {
    this.closeCallback = callback
  }

  onOpen(callback: () => void): void {
    this.openCallback = callback
  }

  // Send message (if needed for bidirectional communication)
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected. Cannot send message:', message)
    }
  }

  // Get connection state
  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }

  getReadyStateString(): string {
    switch (this.getReadyState()) {
      case WebSocket.CONNECTING: return 'CONNECTING'
      case WebSocket.OPEN: return 'OPEN'
      case WebSocket.CLOSING: return 'CLOSING'
      case WebSocket.CLOSED: return 'CLOSED'
      default: return 'UNKNOWN'
    }
  }
}

// Factory function to create WebSocket instances
export const createWebSocket = (): ResearchWebSocket => new ResearchWebSocket()

// Default instance
export const websocket = new ResearchWebSocket()