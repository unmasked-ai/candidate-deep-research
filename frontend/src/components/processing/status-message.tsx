import * as React from "react"
import { cn } from "@/utils/cn"
import type { StatusMessage } from "./types"

interface StatusMessageProps {
  message: StatusMessage
  className?: string
}

const StatusMessageComponent = React.forwardRef<HTMLDivElement, StatusMessageProps>(
  ({ message, className }, ref) => {
    const formatTimestamp = (timestamp: Date): string => {
      return timestamp.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }

    const getMessageIcon = (type: StatusMessage['type']) => {
      switch (type) {
        case 'info':
          return (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        case 'success':
          return (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        case 'warning':
          return (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L3.732 19c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          )
        case 'error':
          return (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        default:
          return null
      }
    }

    const getMessageStyles = (type: StatusMessage['type']) => {
      switch (type) {
        case 'info':
          return {
            container: "border-blue-200 bg-blue-50",
            icon: "text-blue-500",
            text: "text-blue-900",
            timestamp: "text-blue-700"
          }
        case 'success':
          return {
            container: "border-green-200 bg-green-50",
            icon: "text-green-500",
            text: "text-green-900",
            timestamp: "text-green-700"
          }
        case 'warning':
          return {
            container: "border-yellow-200 bg-yellow-50",
            icon: "text-yellow-500",
            text: "text-yellow-900",
            timestamp: "text-yellow-700"
          }
        case 'error':
          return {
            container: "border-red-200 bg-red-50",
            icon: "text-red-500",
            text: "text-red-900",
            timestamp: "text-red-700"
          }
        default:
          return {
            container: "border-gray-200 bg-gray-50",
            icon: "text-gray-500",
            text: "text-gray-900",
            timestamp: "text-gray-700"
          }
      }
    }

    const styles = getMessageStyles(message.type)

    return (
      <div
        ref={ref}
        className={cn(
          "flex items-start space-x-3 p-3 rounded-lg border transition-all duration-200",
          styles.container,
          className
        )}
        role={message.type === 'error' ? 'alert' : 'status'}
        aria-live={message.type === 'error' ? 'assertive' : 'polite'}
      >
        <div className={cn("flex-shrink-0 mt-0.5", styles.icon)}>
          {getMessageIcon(message.type)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <p className={cn("text-sm font-medium", styles.text)}>
              {message.stage}
            </p>
            <time
              dateTime={message.timestamp.toISOString()}
              className={cn("text-xs ml-2 flex-shrink-0", styles.timestamp)}
            >
              {formatTimestamp(message.timestamp)}
            </time>
          </div>
          <p className={cn("text-sm mt-1", styles.text)}>
            {message.message}
          </p>
        </div>
      </div>
    )
  }
)

StatusMessageComponent.displayName = "StatusMessage"

export { StatusMessageComponent as StatusMessage }