export type ThreatColor =
  | 'red'
  | 'orange'
  | 'purple'
  | 'pink'
  | 'yellow'
  | 'indigo'
  | 'teal'
  | 'rose'
  | 'gray'
  | 'violet'
  | 'slate'
  | 'green'

export interface ThreatCategory {
  id: number
  name: string
  icon: string
  color: ThreatColor
  priority: number
  description: string
  mechanism: string
  warningSigns: string
  recommendedAction: string
}

export interface ThreatIntelItem {
  id: string
  title: string
  source: string
  category: string
  date: string
  summary: string
  url?: string
}
