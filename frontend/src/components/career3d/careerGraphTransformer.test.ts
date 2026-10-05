import { describe, expect, it } from 'vitest'
import { transformCareerGraph } from './careerGraphTransformer'
import type { RoleSummary, SimulationPath } from '@/types'

const roles: RoleSummary[] = [
  { id: 'analyst', title: 'Data Analyst', normalized_title: 'data_analyst', domain: 'Data', seniority_level: 2 },
  { id: 'scientist', title: 'Data Scientist', normalized_title: 'data_scientist', domain: 'Data', seniority_level: 3 },
  { id: 'engineer', title: 'Data Engineer', normalized_title: 'data_engineer', domain: 'Data', seniority_level: 3 },
]

function path(id: string, targetId: string, target: RoleSummary, transition_path: string[]): SimulationPath {
  return {
    id,
    simulation_id: 'simulation',
    target_role_id: targetId,
    target_role: target,
    confidence_score: 0.72,
    confidence_label: 'High',
    estimated_months: 18,
    rank: 1,
    engine_metadata: { transition_path, target_role_title: target.title },
    skill_gaps: [],
    roadmap_steps: [],
  }
}

describe('transformCareerGraph', () => {
  it('uses real current and recommended roles and preserves transition routes', () => {
    const result = transformCareerGraph(
      [path('path-1', 'scientist', roles[1], ['data_analyst', 'analytics_engineer', 'data_scientist'])],
      roles,
      roles[0],
    )

    expect(result.nodes[0]).toMatchObject({ title: 'Data Analyst', roleId: 'analyst', kind: 'current' })
    expect(result.nodes.map((node) => node.title)).toEqual([
      'Data Analyst',
      'Analytics Engineer',
      'Data Scientist',
    ])
    expect(result.edges).toHaveLength(2)
    expect(result.edges[0].confidence).toBe(0.72)
  })

  it('keeps independent paths and supports profiles without a current role', () => {
    const result = transformCareerGraph(
      [
        path('path-1', 'scientist', roles[1], ['data_scientist']),
        path('path-2', 'engineer', roles[2], ['data_engineer']),
      ],
      roles,
      null,
    )

    expect(result.nodes.filter((node) => node.kind === 'recommendation')).toHaveLength(2)
    expect(result.edges).toHaveLength(0)
    expect(result.nodes[0]).toMatchObject({ title: 'Current role not set', roleId: null })
    expect(result.nodes.filter((node) => node.kind === 'recommendation').every((node) => node.roleId)).toBe(true)
  })

  it('does not invent connections when the engine reports no catalog transition route', () => {
    const result = transformCareerGraph(
      [path('path-1', 'scientist', roles[1], [])],
      roles,
      roles[0],
    )

    expect(result.nodes.map((node) => node.kind)).toEqual(['current', 'recommendation'])
    expect(result.nodes[1]).toMatchObject({ roleId: 'scientist', position: [1.4, 0, 0] })
    expect(result.edges).toHaveLength(0)
  })

  it('lays out many recommendations in an even, centered layer', () => {
    const manyRoles = Array.from({ length: 10 }, (_, index) => ({
      ...roles[1],
      id: `role-${index}`,
      title: `Career Option ${index + 1}`,
      normalized_title: `career_option_${index + 1}`,
    }))
    const paths = manyRoles.map((role, index) => ({
      ...path(`path-${index + 1}`, role.id, role, ['data_analyst', role.normalized_title]),
      rank: index + 1,
    }))

    const graph = transformCareerGraph(paths, roles.concat(manyRoles), roles[0])
    const current = graph.nodes.find((node) => node.kind === 'current')!
    const recommendations = graph.nodes
      .filter((node) => node.kind === 'recommendation')
      .sort((left, right) => left.position[1] - right.position[1])
    const yPositions = recommendations.map((node) => node.position[1])
    const gaps = yPositions.slice(1).map((position, index) => position - yPositions[index])

    expect(current.position[0]).toBeLessThan(0)
    expect(current.position[1]).toBe(0)
    expect(recommendations).toHaveLength(10)
    expect(new Set(recommendations.map((node) => node.position[0])).size).toBe(1)
    expect(yPositions[0]).toBeCloseTo(-yPositions[yPositions.length - 1])
    expect(gaps.every((gap) => Math.abs(gap - gaps[0]) < 0.001)).toBe(true)
    expect(
      recommendations.find((node) => node.path?.rank === 1)!.position[1],
    ).toBeGreaterThan(recommendations.find((node) => node.path?.rank === 10)!.position[1])
    expect(graph.edges).toHaveLength(10)
  })

  it('shares common transition roles and places later steps on subsequent layers', () => {
    const analyticsLead = {
      ...roles[1],
      id: 'analytics-lead',
      title: 'Analytics Lead',
      normalized_title: 'analytics_lead',
    }
    const graph = transformCareerGraph(
      [
        {
          ...path('path-1', 'scientist', roles[1], [
            'data_analyst',
            'data_engineer',
            'data_scientist',
          ]),
          rank: 1,
        },
        {
          ...path('path-2', analyticsLead.id, analyticsLead, [
            'data_analyst',
            'data_engineer',
            'analytics_lead',
          ]),
          rank: 2,
        },
      ],
      [...roles, analyticsLead],
      roles[0],
    )
    const transitions = graph.nodes.filter((node) => node.kind === 'transition')
    const recommendations = graph.nodes.filter((node) => node.kind === 'recommendation')

    expect(transitions).toHaveLength(1)
    expect(recommendations).toHaveLength(2)
    expect(transitions[0].position[0]).toBeGreaterThan(graph.nodes[0].position[0])
    expect(recommendations.find((node) => node.title === 'Analytics Lead')!.position[0])
      .toBeGreaterThan(transitions[0].position[0])
    expect(graph.edges).toHaveLength(3)
    expect(graph.edges.find((edge) => edge.pathIds.length === 2)).toBeDefined()
  })
})
