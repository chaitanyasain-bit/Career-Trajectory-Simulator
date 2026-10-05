import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Html, Line, OrbitControls } from '@react-three/drei'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode, RefObject } from 'react'
import { Component } from 'react'
import type { Mesh, PerspectiveCamera, QuadraticBezierCurve3 } from 'three'
import { QuadraticBezierCurve3 as BezierCurve, Quaternion, Vector3 } from 'three'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { ArrowUpRight, Expand, GitCompareArrows, RotateCcw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '@/services/api'
import { transformCareerGraph } from '@/components/career3d/careerGraphTransformer'
import type { CareerGraphEdge, CareerGraphNode } from '@/components/career3d/careerGraphTransformer'
import type { RoleSummary, SimulationResult, UserProfile } from '@/types'

export interface CareerTrajectory3DProps {
  simulation: SimulationResult
  profile: UserProfile
  roles: RoleSummary[]
  compact?: boolean
}

const COLORS = {
  current: '#0f766e',
  recommended: '#b45309',
  high: '#0d9488',
  medium: '#d97706',
  low: '#64748b',
  selected: '#7c3aed',
  transition: '#2563eb',
}

function supportsWebGL(): boolean {
  if (typeof document === 'undefined') return false
  try {
    const canvas = document.createElement('canvas')
    return Boolean(canvas.getContext('webgl2') || canvas.getContext('webgl'))
  } catch {
    return false
  }
}

function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () =>
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )
  useEffect(() => {
    if (typeof window === 'undefined') return undefined
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReduced(media.matches)
    media.addEventListener?.('change', update)
    return () => media.removeEventListener?.('change', update)
  }, [])
  return reduced
}

interface SceneProps {
  nodes: CareerGraphNode[]
  edges: CareerGraphEdge[]
  selectedNodeId: string
  selectedPathId: string | undefined
  reducedMotion: boolean
  onSelect: (node: CareerGraphNode) => void
  controlsRef: RefObject<OrbitControlsImpl>
}

function CareerScene({
  nodes,
  edges,
  selectedNodeId,
  selectedPathId,
  reducedMotion,
  onSelect,
  controlsRef,
}: SceneProps) {
  const { camera, size } = useThree()
  useEffect(() => {
    const perspectiveCamera = camera as PerspectiveCamera
    const aspect = size.width / Math.max(size.height, 1)
    const xValues = nodes.map((node) => node.position[0])
    const yValues = nodes.map((node) => node.position[1])
    const graphWidth = Math.max(2, Math.max(...xValues) - Math.min(...xValues) + 3)
    const graphHeight = Math.max(2, Math.max(...yValues) - Math.min(...yValues) + 2.2)
    const tangent = Math.tan((perspectiveCamera.fov * Math.PI) / 360)
    const fitDistance = Math.max(
      graphHeight / (2 * tangent),
      graphWidth / (2 * tangent * Math.max(aspect, 0.65)),
    ) * 1.12
    const targetX = (Math.max(...xValues) + Math.min(...xValues)) / 2
    const targetY = (Math.max(...yValues) + Math.min(...yValues)) / 2
    perspectiveCamera.position.set(targetX, targetY, fitDistance)
    perspectiveCamera.updateProjectionMatrix()
    if (controlsRef.current) {
      controlsRef.current.target.set(targetX, targetY, 0)
      controlsRef.current.minDistance = Math.max(3, fitDistance * 0.55)
      controlsRef.current.maxDistance = Math.max(24, fitDistance * 3)
      controlsRef.current.saveState()
      controlsRef.current.update()
    }
  }, [camera, controlsRef, nodes, size.height, size.width])

  return (
    <>
      <color attach="background" args={['#f8fbfb']} />
      <ambientLight intensity={1.35} />
      <directionalLight position={[4, 7, 8]} intensity={1.65} />
      {edges.map((edge) => (
        <CareerConnection
          key={edge.id}
          edge={edge}
          selected={Boolean(selectedPathId && edge.pathIds.includes(selectedPathId))}
        />
      ))}
      {nodes.map((node) => (
        <CareerNode
          key={node.id}
          node={node}
          selected={node.id === selectedNodeId}
          reducedMotion={reducedMotion}
          onSelect={onSelect}
        />
      ))}
      <OrbitControls
        ref={controlsRef}
        makeDefault
        enableRotate
        enableZoom
        enablePan
        screenSpacePanning
        enableDamping={!reducedMotion}
        dampingFactor={0.08}
        target={[0, 0, 0]}
      />
    </>
  )
}

function CareerConnection({ edge, selected }: { edge: CareerGraphEdge; selected: boolean }) {
  const start = new Vector3(...edge.from)
  const end = new Vector3(...edge.to)
  const direction = end.clone().sub(start).normalize()
  start.addScaledVector(direction, edge.fromRadius + 0.04)
  end.addScaledVector(direction, -(edge.toRadius + 0.04))
  const middle = start.clone().lerp(end, 0.5)
  middle.y += (end.y - start.y) * 0.08
  const curve: QuadraticBezierCurve3 = new BezierCurve(start, middle, end)
  const points = curve.getPoints(24)
  const markerPosition = curve.getPoint(0.84)
  const markerDirection = curve.getTangent(0.84).normalize()
  const markerOrientation = new Quaternion().setFromUnitVectors(
    new Vector3(0, 1, 0),
    markerDirection,
  )
  const edgeColor = selected
    ? COLORS.selected
    : edge.confidence >= 0.7
      ? '#99c7c1'
      : edge.confidence >= 0.45
        ? '#e8cf9f'
        : '#cbd5e1'
  return (
    <group>
      <Line
        points={points}
        color={edgeColor}
        lineWidth={selected ? 2.2 : 1}
        transparent
        opacity={selected ? 0.95 : 0.48}
      />
      <mesh position={markerPosition} quaternion={markerOrientation}>
        <coneGeometry args={[selected ? 0.065 : 0.05, selected ? 0.18 : 0.14, 8]} />
        <meshBasicMaterial color={edgeColor} transparent opacity={selected ? 0.95 : 0.65} />
      </mesh>
    </group>
  )
}

function nodeColor(node: CareerGraphNode): string {
  if (node.kind === 'current') return COLORS.current
  if (node.kind === 'transition') return COLORS.transition
  if (node.path?.rank === 1) return COLORS.recommended
  const score = node.path?.confidence_score ?? 0
  return score >= 0.7 ? COLORS.high : score >= 0.45 ? COLORS.medium : COLORS.low
}

function CareerNode({
  node,
  selected,
  reducedMotion,
  onSelect,
}: {
  node: CareerGraphNode
  selected: boolean
  reducedMotion: boolean
  onSelect: SceneProps['onSelect']
}) {
  const mesh = useRef<Mesh>(null)
  const color = nodeColor(node)
  const radius = node.kind === 'current' ? 0.4 : node.kind === 'recommendation' ? 0.34 : 0.25

  useFrame(({ clock }) => {
    if (mesh.current && !reducedMotion) {
      mesh.current.position.y = node.position[1] + Math.sin(clock.elapsedTime * 0.55 + node.position[0]) * 0.018
    }
  })

  return (
    <group position={node.position}>
      {selected && (
        <mesh>
          <torusGeometry args={[radius + 0.1, 0.022, 8, 40]} />
          <meshBasicMaterial color={COLORS.selected} />
        </mesh>
      )}
      <mesh
        ref={mesh}
        onClick={(event) => {
          event.stopPropagation()
          onSelect(node)
        }}
        onPointerOver={(event) => {
          event.stopPropagation()
          document.body.style.cursor = 'pointer'
        }}
        onPointerOut={() => { document.body.style.cursor = 'default' }}
      >
        <sphereGeometry args={[radius, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.16}
          roughness={0.34}
          metalness={0.08}
        />
      </mesh>
      {node.kind !== 'transition' || selected ? (
        <Html
          position={[
            node.kind === 'current' ? -0.72 : node.kind === 'transition' ? -1.2 : 0,
            radius + 0.2,
            0,
          ]}
          center
          distanceFactor={11}
          occlude={false}
        >
          <button
            type="button"
            title={node.title}
            className={`block max-w-36 truncate whitespace-nowrap rounded-full border px-2.5 py-1 text-[10px] font-semibold shadow-sm ${
              selected
                ? 'border-violet-200 bg-violet-50 text-violet-900'
                : node.kind === 'current'
                  ? 'border-teal-200 bg-white text-teal-900'
                  : node.kind === 'transition'
                    ? 'border-blue-100 bg-white/90 text-blue-800'
                    : 'border-slate-200 bg-white/95 text-slate-700'
            }`}
            onClick={(event) => {
              event.stopPropagation()
              onSelect(node)
            }}
          >
            {node.kind === 'current' ? 'YOU · ' : ''}{node.title}
          </button>
        </Html>
      ) : null}
    </group>
  )
}

class SceneErrorBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    return this.state.hasError ? this.props.fallback : this.props.children
  }
}

export function CareerTrajectory3D({
  simulation,
  profile,
  roles,
  compact = false,
}: CareerTrajectory3DProps) {
  const [layoutCompact, setLayoutCompact] = useState(
    () => compact || (typeof window !== 'undefined' && window.matchMedia('(max-width: 639px)').matches),
  )
  useEffect(() => {
    const updateLayout = () =>
      setLayoutCompact(compact || window.matchMedia('(max-width: 639px)').matches)
    window.addEventListener('resize', updateLayout)
    return () => window.removeEventListener('resize', updateLayout)
  }, [compact])
  const currentRole = roles.find((role) => role.id === profile.current_role_id) ?? null
  const graph = useMemo(
    () => transformCareerGraph(simulation.paths, roles, currentRole, layoutCompact),
    [simulation.paths, roles, currentRole, layoutCompact],
  )
  const firstRecommendation = graph.nodes.find((node) => node.kind === 'recommendation')
  const [selectedNode, setSelectedNode] = useState<CareerGraphNode | null>(firstRecommendation ?? null)
  const activeNode = graph.nodes.find((node) => node.id === selectedNode?.id) ?? firstRecommendation
  const selectedPath = activeNode?.path ?? simulation.paths[0]
  const selectedRole = useQuery({
    queryKey: ['role', activeNode?.roleId ?? selectedPath?.target_role_id],
    queryFn: () => api.getRole(activeNode?.roleId ?? selectedPath!.target_role_id),
    enabled: Boolean(activeNode?.roleId ?? selectedPath?.target_role_id),
    staleTime: 5 * 60_000,
  })
  const reducedMotion = useReducedMotion()
  const [webglAvailable] = useState(supportsWebGL)
  const [fullscreen, setFullscreen] = useState(false)
  const stageRef = useRef<HTMLDivElement>(null)
  const controlsRef = useRef<OrbitControlsImpl>(null)
  const gapBySkill = new Map((selectedPath?.skill_gaps ?? []).map((gap) => [gap.skill_id, gap]))
  const profileSkillLevel = new Map(profile.user_skills.map((skill) => [skill.skill_id, skill.proficiency_level]))
  const requirements = selectedRole.data?.skill_requirements ?? []
  const coveredRequirementCount = requirements.filter((requirement) => {
    const currentLevel =
      gapBySkill.get(requirement.skill_id)?.current_proficiency ??
      profileSkillLevel.get(requirement.skill_id) ??
      0
    return currentLevel >= requirement.required_proficiency
  }).length
  const coveragePercent = requirements.length
    ? Math.round((coveredRequirementCount / requirements.length) * 100)
    : null
  const isCurrentNode = activeNode?.kind === 'current'
  const selectedNodeIsRecommendation = activeNode?.kind === 'recommendation'

  const selectNode = (node: CareerGraphNode) => setSelectedNode(node)
  const resetView = () => controlsRef.current?.reset()
  const toggleFullscreen = async () => {
    if (!stageRef.current) return
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    } else if (stageRef.current.requestFullscreen) {
      await stageRef.current.requestFullscreen()
    }
    setFullscreen(Boolean(document.fullscreenElement))
  }
  useEffect(() => {
    const updateFullscreen = () => setFullscreen(Boolean(document.fullscreenElement))
    document.addEventListener('fullscreenchange', updateFullscreen)
    return () => document.removeEventListener('fullscreenchange', updateFullscreen)
  }, [])

  return (
    <section
      ref={stageRef}
      className={`overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm ${fullscreen ? 'h-screen w-screen p-6' : ''}`}
      aria-labelledby="career-map-title"
    >
      <div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center sm:justify-between sm:px-5">
        <div>
          <p className="eyebrow">Career intelligence · Career map</p>
          <h2 id="career-map-title" className="mt-1 text-lg font-bold text-slate-950">
            Your trajectory
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            {simulation.paths.length} paths · confidence and transitions from this saved simulation
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-quiet" onClick={resetView} disabled={!webglAvailable} aria-label="Reset career graph view">
            <RotateCcw className="h-4 w-4" /> Reset view
          </button>
          <button
            type="button"
            className="btn-quiet"
            onClick={() => void toggleFullscreen()}
            disabled={!webglAvailable || !stageRef.current?.requestFullscreen}
            aria-label={fullscreen ? 'Exit expanded career graph' : 'Expand career graph'}
          >
            <Expand className="h-4 w-4" /> {fullscreen ? 'Exit expand' : 'Expand'}
          </button>
        </div>
      </div>

      <div className={`grid gap-4 p-3 sm:p-5 xl:grid-cols-[minmax(0,1.55fr)_minmax(280px,.8fr)] ${fullscreen ? 'h-[calc(100%-76px)] overflow-auto' : ''}`}>
        <div className="min-w-0">
          <div className="mb-2 flex items-center justify-between gap-2 px-1 text-[9px] font-bold uppercase tracking-[0.12em] text-slate-400 sm:text-[10px]">
            <span>Current role</span>
            <span aria-hidden="true" className="mx-1 h-px flex-1 bg-slate-200" />
            <span>Next options</span>
            <span aria-hidden="true" className="mx-1 h-px flex-1 bg-slate-200" />
            <span>Advanced options</span>
          </div>
          <div className={`${compact ? 'h-[300px] sm:h-[360px]' : 'h-[360px] sm:h-[430px]'} overflow-hidden rounded-xl border border-slate-100 bg-[#f8fbfb]`}>
            {webglAvailable ? (
              <SceneErrorBoundary fallback={<WebGLFallback />}>
                <Canvas
                  camera={{ position: [0, 0, 11], fov: 48 }}
                  dpr={[1, 1.5]}
                  frameloop={reducedMotion ? 'demand' : 'always'}
                  gl={{ antialias: true, alpha: false }}
                >
                  <CareerScene
                    nodes={graph.nodes}
                    edges={graph.edges}
                    selectedNodeId={activeNode?.id ?? ''}
                    selectedPathId={selectedPath?.id}
                    reducedMotion={reducedMotion}
                    onSelect={selectNode}
                    controlsRef={controlsRef}
                  />
                </Canvas>
              </SceneErrorBoundary>
            ) : <WebGLFallback />}
          </div>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 px-1 text-[11px] text-slate-600" aria-label="Career map legend">
            <LegendDot color={COLORS.current} label="Current role" />
            <LegendDot color={COLORS.recommended} label="Recommended" />
            <LegendDot color={COLORS.high} label="Strong fit" />
            <LegendDot color={COLORS.medium} label="Developing fit" />
            <LegendDot color={COLORS.low} label="Lower fit" />
            <LegendDot color={COLORS.transition} label="Transition" />
            <span className="text-slate-400">Drag to rotate · scroll to zoom · right-drag to pan</span>
          </div>
        </div>

        <aside className="rounded-xl border border-slate-100 bg-slate-50/70 p-4" aria-live="polite">
          {activeNode && selectedPath ? (
            <>
              <p className="eyebrow">{selectedNodeIsRecommendation ? 'Recommended destination' : isCurrentNode ? 'Starting point' : 'Transition role'}</p>
              <h3 className="mt-1 text-lg font-bold text-slate-950">{activeNode.title}</h3>
              {isCurrentNode ? (
                <p className="mt-1 text-xs text-slate-500">Your current role anchors the career routes generated from your profile.</p>
              ) : activeNode.kind !== 'recommendation' ? (
                <p className="mt-1 text-xs text-slate-500">
                  Route recommendation: {selectedPath.target_role?.title ?? selectedPath.engine_metadata.target_role_title ?? 'Career path'}
                </p>
              ) : null}
              {!isCurrentNode && (
                <div className="mt-3 flex items-center gap-2">
                  <span className="rounded-full bg-teal-50 px-2.5 py-1 text-xs font-bold text-teal-800">
                    {Math.round(selectedPath.confidence_score * 100)}% {activeNode.kind === 'transition' ? 'route confidence' : 'confidence'}
                  </span>
                  <span className="text-xs text-slate-500">Rank #{selectedPath.rank}</span>
                </div>
              )}
              {!isCurrentNode && (
                <p className="mt-2 text-xs text-slate-600">
                  Estimated transition: {selectedPath.estimated_months
                    ? `about ${selectedPath.estimated_months} months`
                    : 'timeline not estimated'}
                </p>
              )}
              <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                {isCurrentNode
                  ? 'Career starting point'
                  : activeNode.kind === 'transition'
                    ? 'Why this route is recommended'
                    : 'Why it is recommended'}
              </p>
              <ul className="mt-2 space-y-1.5 text-sm leading-5 text-slate-700">
                {(isCurrentNode
                  ? ['Your saved profile identifies this as your current role.']
                  : selectedPath.engine_metadata.why_recommended ?? []
                ).slice(0, 3).map((reason, index) => (
                  <li key={`${index}-${reason}`} className="flex gap-2"><span className="text-teal-700">•</span>{reason}</li>
                ))}
                {!isCurrentNode && !selectedPath.engine_metadata.why_recommended?.length && (
                  <li>{selectedPath.engine_metadata.confidence_factors?.[0]?.explanation ?? 'This path was ranked using your profile and career-transition data.'}</li>
                )}
              </ul>

              <div className="mt-4 flex items-center justify-between gap-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Required skills
                </p>
                {selectedRole.isLoading && <span className="text-[11px] text-slate-400">Loading catalog…</span>}
              </div>
              {selectedRole.error ? (
                <p className="mt-2 text-xs text-rose-700" role="alert">
                  Could not load role requirements.{' '}
                  <button type="button" className="font-semibold underline" onClick={() => void selectedRole.refetch()}>
                    Retry
                  </button>
                </p>
              ) : (
                <>
                  {coveragePercent !== null && (
                    <div className="mt-2 rounded-lg border border-slate-100 bg-white px-3 py-2">
                      <div className="flex items-center justify-between gap-2 text-[11px] text-slate-600">
                        <span>Current skill coverage</span>
                        <span className="font-semibold text-slate-800">
                          {coveredRequirementCount}/{requirements.length} · {coveragePercent}%
                        </span>
                      </div>
                      <div
                        className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100"
                        role="progressbar"
                        aria-label="Current required skill coverage"
                        aria-valuemin={0}
                        aria-valuemax={requirements.length}
                        aria-valuenow={coveredRequirementCount}
                      >
                        <div
                          className="h-full rounded-full bg-teal-600 transition-[width]"
                          style={{ width: `${coveragePercent}%` }}
                        />
                      </div>
                    </div>
                  )}
                  <div className="mt-2 flex flex-wrap gap-1.5">
                  {requirements.slice(0, 8).map((requirement) => {
                    const gap = gapBySkill.get(requirement.skill_id)
                    const proficiency =
                      gap?.current_proficiency ??
                      profileSkillLevel.get(requirement.skill_id) ??
                      0
                    const isMet = proficiency >= requirement.required_proficiency
                    return (
                      <span key={requirement.skill_id} className={`rounded-md px-2 py-1 text-[11px] ${!isCurrentNode && !isMet ? 'bg-amber-50 text-amber-900' : 'bg-white text-slate-700'}`}>
                        {requirement.skill?.name ?? 'Skill'} · {proficiency}/{requirement.required_proficiency}
                      </span>
                    )
                  })}
                  {!selectedRole.isLoading && !selectedRole.data?.skill_requirements?.length && (
                    <span className="text-xs text-slate-500">No role requirements are available for this catalog entry.</span>
                  )}
                  </div>
                </>
              )}

              <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                {isCurrentNode
                  ? 'Destination skill gaps'
                  : activeNode.kind === 'transition'
                    ? `Destination skill gaps · ${selectedPath.skill_gaps.length}`
                    : `Skill gaps · ${selectedPath.skill_gaps.length}`}
              </p>
              <p className="mt-1 text-sm text-slate-700">
                {isCurrentNode
                  ? `Select a recommended role to view its gaps. Top path: ${selectedPath.skill_gaps.slice(0, 3).map((gap) => gap.skill?.name ?? 'Skill').join(' · ') || 'no identified gaps'}.`
                  : `${activeNode.kind === 'transition' ? 'For the recommended destination: ' : ''}${selectedPath.skill_gaps.slice(0, 3).map((gap) => gap.skill?.name ?? 'Skill').join(' · ') || 'No identified proficiency gaps'}${selectedPath.skill_gaps.length > 3 ? ` · +${selectedPath.skill_gaps.length - 3} more` : ''}`}
              </p>

              <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Career transition</p>
              <p className="mt-1 text-sm leading-5 text-slate-700">
                {isCurrentNode
                  ? 'Select a recommended role to explore its transition route.'
                  : (selectedPath.engine_metadata.transition_path ?? []).length
                    ? (selectedPath.engine_metadata.transition_path ?? []).map((name) => displayRole(name)).join(' → ')
                    : 'No catalog transition route is available; this role is shown as an alternative.'}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  className="btn-quiet"
                  to={isCurrentNode && activeNode.roleId
                    ? `/careers/${activeNode.roleId}`
                    : `/careers/${selectedPath.target_role_id}?simulationId=${simulation.id}`}
                >
                  Career details <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
                {isCurrentNode
                  ? <span className="self-center text-xs text-slate-500">Roadmaps are generated for recommended roles.</span>
                  : <Link className="btn-quiet" to={`/roadmap/${selectedPath.id}`}>
                    Open roadmap <ArrowUpRight className="h-3.5 w-3.5" />
                  </Link>}
                {!isCurrentNode && (
                  <Link
                    className="btn-quiet"
                    to={`/comparison?simulationId=${simulation.id}&pathId=${selectedPath.id}`}
                  >
                    <GitCompareArrows className="h-3.5 w-3.5" /> Compare
                  </Link>
                )}
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">Select a career node or path to explore its details.</p>
          )}
        </aside>
      </div>

      <div className="border-t border-slate-100 px-4 py-4 sm:px-5">
        <div className="mb-3 flex items-baseline justify-between gap-3">
          <h3 className="text-sm font-bold text-slate-900">Explore paths without 3D controls</h3>
          <span className="text-xs text-slate-500">Accessible career map</span>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {simulation.paths.map((path) => {
            const node = graph.nodes.find((item) => item.path?.id === path.id && item.kind === 'recommendation')
            if (!node) return null
            const selected = activeNode?.path?.id === path.id
            return (
              <button
                key={path.id}
                type="button"
                aria-pressed={selected}
                onClick={() => selectNode(node)}
                className={`flex min-w-0 items-center justify-between gap-3 rounded-lg border px-3 py-2 text-left transition ${
                  selected ? 'border-violet-300 bg-violet-50' : 'border-slate-200 bg-white hover:border-teal-200'
                }`}
              >
                <span className="min-w-0">
                  <span className="block truncate text-sm font-semibold text-slate-800">{node.title}</span>
                  <span className="text-[11px] text-slate-500">Rank #{path.rank} · {path.skill_gaps.length} gaps</span>
                </span>
                <span className="shrink-0 text-sm font-bold text-slate-700">{Math.round(path.confidence_score * 100)}%</span>
              </button>
            )
          })}
        </div>
        {graph.nodes.some((node) => node.kind === 'transition') && (
          <div className="mt-4">
            <h4 className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
              Intermediate roles in catalog routes
            </h4>
            <div className="flex flex-wrap gap-2">
              {graph.nodes.filter((node) => node.kind === 'transition').map((node) => {
                const selected = activeNode?.id === node.id
                const destination = node.path?.target_role?.title
                  ?? node.path?.engine_metadata.target_role_title
                  ?? 'recommended role'
                return (
                  <button
                    key={node.id}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => selectNode(node)}
                    className={`rounded-lg border px-3 py-2 text-left text-xs transition ${
                      selected
                        ? 'border-violet-300 bg-violet-50 text-violet-900'
                        : 'border-blue-100 bg-white text-slate-700 hover:border-blue-300'
                    }`}
                  >
                    <span className="block font-semibold">{node.title}</span>
                    <span className="mt-0.5 block text-[10px] text-slate-500">
                      On route to {destination}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

function displayRole(normalizedTitle: string): string {
  return normalizedTitle.split(/[_\s-]+/).filter(Boolean)
    .map((part) => part.charAt(0).toLocaleUpperCase() + part.slice(1)).join(' ')
}

function WebGLFallback() {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center" role="status">
      <p className="font-semibold text-slate-800">Accessible career map</p>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
        3D rendering is unavailable in this browser. Use the career-path list below to explore the same simulation results.
      </p>
    </div>
  )
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />{label}</span>
}
