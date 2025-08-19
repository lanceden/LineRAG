"use client"

import React, { forwardRef } from 'react'
import { type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface InputWithIconProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon: LucideIcon
  error?: string
  label?: string
}

interface TextAreaWithIconProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  icon: LucideIcon
  error?: string
  label?: string
}

export const InputWithIcon = forwardRef<HTMLInputElement, InputWithIconProps>(
  ({ icon: Icon, error, label, className, id, ...props }, ref) => {
    return (
      <div>
        {label && (
          <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
            <span dangerouslySetInnerHTML={{ __html: label.replace(/\*/, '<span class="text-red-500">*</span>') }} />
          </label>
        )}
        <div className="relative">
          <Icon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            ref={ref}
            id={id}
            className={cn(
              'pl-10 pr-3 w-full py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              error ? 'border-red-300' : 'border-gray-300',
              className
            )}
            {...props}
          />
        </div>
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
      </div>
    )
  }
)

InputWithIcon.displayName = 'InputWithIcon'

export const TextAreaWithIcon = forwardRef<HTMLTextAreaElement, TextAreaWithIconProps>(
  ({ icon: Icon, error, label, className, id, rows = 2, ...props }, ref) => {
    return (
      <div>
        {label && (
          <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
            <span dangerouslySetInnerHTML={{ __html: label.replace(/\*/, '<span class="text-red-500">*</span>') }} />
          </label>
        )}
        <div className="relative">
          <Icon className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <textarea
            ref={ref}
            id={id}
            rows={rows}
            className={cn(
              'pl-10 pr-3 w-full py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none',
              error ? 'border-red-300' : 'border-gray-300',
              className
            )}
            {...props}
          />
        </div>
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
      </div>
    )
  }
)

TextAreaWithIcon.displayName = 'TextAreaWithIcon'