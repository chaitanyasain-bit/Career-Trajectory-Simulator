import type { RoleSummary, SimulationPath } from '@/types'

export type GraphPosition = [number, number, number]

export interface CareerGraphNode {
  id: string
  title: string
  roleId: string | null
  kind: 'current' | 'transition' | 'recommendation'
  position: GraphPosition
  path: SimulationPath | null
}

export interface CareerGraphEdge {
  id: string
  from: GraphPosition
  to: GraphPosition
  fromRadius: number
  toRadius: number
  confidence: number
  pathIds: string[]
}

export interface CareerGraph {
  nodes: CareerGraphNode[]
  edges: CareerGraphEdge[]
}

interface DraftNode {
  id: string
  title: string
  roleId: string | null
  kind: CareerGraphNode['kind']
  parentId: string | null
  depth: number
  path: SimulationPath | null
  rank: number
  children: Set<string>
}

interface DraftEdge {
  id: string
  fromId: string
  toId: string
  confidence: number
  pathIds: Set<string>
}

function normalized(value: string): string {
  return value.trim().toLocaleLowerCase().replace(/[\s-]+/g, '_')
}

function displayName(value: string): string {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toLocaleUpperCase() + part.slice(1))
    .join(' ')
}

function nodeRadius(kind: CareerGraphNode['kind']): number {
  if (kind === 'current') return 0.4
  if (kind === 'recommendation') return 0.34
  return 0.25
}

export function transformCareerGraph(
  paths: SimulationPath[],
  roles: RoleSummary[],
  currentRole: RoleSummary | null,
  compact = false,
): CareerGraph {
  const roleByNormalizedTitle = new Map(
    roles.map((role) => [normalized(role.normalized_title || role.title), role]),
  )
  const drafts = new Map<string, DraftNode>()
  const edgesByKey = new Map<string, DraftEdge>()
  const rootId = 'current-role'

  drafts.set(rootId, {
    id: rootId,
    title: currentRole?.title ?? 'Current role not set',
    roleId: currentRole?.id ?? null,
    kind: 'current',
    parentId: null,
    depth: 0,
    path: null,
    rank: 0,
    children: new Set(),
  })

  const orderedPaths = paths
    .map((path, index) => ({ path, index }))
    .sort((left, right) => left.path.rank - right.path.rank || left.index - right.index)

  for (const { path } of orderedPaths) {
    const targetRole = path.target_role ?? null
    const targetTitle =
      targetRole?.title ?? path.engine_metadata.target_role_title ?? 'Recommended role'
    const targetNormalized =
      targetRole?.normalized_title ??
      (typeof path.engine_metadata.target_role_title === 'string'
        ? normalized(path.engine_metadata.target_role_title)
        : '')
    const targetCatalogRole =
      roles.find((role) => role.id === path.target_role_id) ??
      roleByNormalizedTitle.get(normalized(targetNormalized))
    const rank = Number.isFinite(path.rank) ? path.rank : Number.MAX_SAFE_INTEGER
    const reportedRoute = (path.engine_metadata.transition_path ?? [])
      .map((roleName) => roleName.trim())
      .filter(Boolean)
    const hasCatalogRoute =
      currentRole !== null &&
      reportedRoute.length >= 2 &&
      normalized(reportedRoute[0]) === normalized(currentRole.normalized_title || currentRole.title) &&
      normalized(reportedRoute[reportedRoute.length - 1]) === normalized(targetNormalized)

    let parentId = rootId
    const route = hasCatalogRoute ? reportedRoute.slice(1) : []
    route.forEach((routeRole, routeIndex) => {
      const isRecommendation = routeIndex === route.length - 1
      const catalogRole =
        (isRecommendation ? targetCatalogRole : undefined) ??
        roleByNormalizedTitle.get(normalized(routeRole))
      const title = isRecommendation
        ? targetTitle
        : catalogRole?.title ?? displayName(routeRole)
      const roleId = catalogRole?.id ?? (isRecommendation ? path.target_role_id : null)
      const childKey = isRecommendation
        ? `recommendation:${roleId}:${parentId}`
        : `transition:${normalized(routeRole)}:${parentId}`
      const childId = childKey
      let draft = drafts.get(childId)

      if (!draft) {
        draft = {
          id: childId,
          title,
          roleId,
          kind: isRecommendation ? 'recommendation' : 'transition',
          parentId,
          depth: (drafts.get(parentId)?.depth ?? 0) + 1,
          path,
          rank,
          children: new Set(),
        }
        drafts.set(childId, draft)
      } else if (
        draft.path === null ||
        rank < (Number.isFinite(draft.path.rank) ? draft.path.rank : Number.MAX_SAFE_INTEGER)
      ) {
        draft.path = path
        draft.rank = rank
      }

      drafts.get(parentId)?.children.add(childId)
      const edgeKey = `${parentId}->${childId}`
      let edge = edgesByKey.get(edgeKey)
      if (!edge) {
        edge = {
          id: edgeKey,
          fromId: parentId,
          toId: childId,
          confidence: path.confidence_score,
          pathIds: new Set(),
        }
        edgesByKey.set(edgeKey, edge)
      }
      edge.confidence = Math.max(edge.confidence, path.confidence_score)
      edge.pathIds.add(path.id)
      parentId = childId
    })

    if (!hasCatalogRoute) {
      const childId = `alternative:${path.id}`
      drafts.set(childId, {
        id: childId,
        title: targetTitle,
        roleId: targetCatalogRole?.id ?? path.target_role_id,
        kind: 'recommendation',
        parentId: rootId,
        depth: 1,
        path,
        rank,
        children: new Set(),
      })
      drafts.get(rootId)?.children.add(childId)
    }
  }

  const minimumRank = (nodeId: string): number => {
    const node = drafts.get(nodeId)
    if (!node) return Number.MAX_SAFE_INTEGER
    if (node.kind === 'recommendation' || node.children.size === 0) return node.rank
    return Math.min(...Array.from(node.children, minimumRank))
  }

  const orderedLeaves: string[] = []
  const visit = (nodeId: string) => {
    const node = drafts.get(nodeId)
    if (!node) return
    if (node.kind === 'recommendation' || node.children.size === 0) {
      if (node.kind === 'recommendation') orderedLeaves.push(nodeId)
      return
    }
    const children = Array.from(node.children).sort((leftId, rightId) => {
      const rankDifference = minimumRank(leftId) - minimumRank(rightId)
      if (rankDifference !== 0) return rankDifference
      return (drafts.get(leftId)?.title ?? '').localeCompare(drafts.get(rightId)?.title ?? '')
    })
    children.forEach(visit)
  }
  visit(rootId)

  const maxDepth = Math.max(1, ...Array.from(drafts.values(), (node) => node.depth))
  const horizontalSpacing = compact ? 2.2 : 2.8
  const verticalSpacing = compact ? 1.05 : 1.25
  const rootX = -(maxDepth * horizontalSpacing) / 2
  const yByNode = new Map<string, number>()
  orderedLeaves.forEach((nodeId, index) => {
    yByNode.set(nodeId, ((orderedLeaves.length - 1) / 2 - index) * verticalSpacing)
  })

  const positionFor = (nodeId: string): GraphPosition => {
    const node = drafts.get(nodeId)
    if (!node) return [0, 0, 0]
    const y = node.kind === 'current' ? 0 : yByNode.get(nodeId) ?? (() => {
      const descendantYs = Array.from(node.children, positionFor).map((position) => position[1])
      return descendantYs.length
        ? descendantYs.reduce((sum, value) => sum + value, 0) / descendantYs.length
        : 0
    })()
    yByNode.set(nodeId, y)
    return [rootX + node.depth * horizontalSpacing, y, 0]
  }

  const nodes: CareerGraphNode[] = Array.from(drafts.values())
    .map((node) => ({
      id: node.id,
      title: node.title,
      roleId: node.roleId,
      kind: node.kind,
      position: positionFor(node.id),
      path: node.path,
    }))
    .sort((left, right) => {
      if (left.kind === 'current') return -1
      if (right.kind === 'current') return 1
      return left.position[0] - right.position[0] || left.position[1] - right.position[1]
    })
  const nodeById = new Map(nodes.map((node) => [node.id, node]))
  const edges: CareerGraphEdge[] = Array.from(edgesByKey.values()).map((edge) => {
    const fromNode = nodeById.get(edge.fromId)
    const toNode = nodeById.get(edge.toId)
    return {
      id: edge.id,
      from: fromNode?.position ?? [0, 0, 0],
      to: toNode?.position ?? [0, 0, 0],
      fromRadius: nodeRadius(fromNode?.kind ?? 'current'),
      toRadius: nodeRadius(toNode?.kind ?? 'recommendation'),
      confidence: edge.confidence,
      pathIds: Array.from(edge.pathIds),
    }
  })

  return { nodes, edges }
}
