export interface AgentStatusItem {
  id: string
  label: string
  status: 'healthy' | 'degraded' | 'offline'
  description: string
}

export interface CommandAction {
  id: string
  label: string
  icon?: string
  intent: 'primary' | 'secondary' | 'ghost'
  disabled?: boolean
}

export interface SidebarNavItem {
  id: string
  label: string
  icon?: string
  active: boolean
  badge?: string
}

export interface StatePanelProps {
  kind: 'loading' | 'empty' | 'error'
  title: string
  message: string
  actionLabel?: string
}
