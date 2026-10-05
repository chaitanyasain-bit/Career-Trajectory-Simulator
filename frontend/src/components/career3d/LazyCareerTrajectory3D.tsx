import { lazy, Suspense } from 'react'
import type { CareerTrajectory3DProps } from '@/components/career3d/CareerTrajectory3D'

const CareerTrajectory3D = lazy(() =>
  import('@/components/career3d/CareerTrajectory3D').then((module) => ({
    default: module.CareerTrajectory3D,
  })),
)

export function LazyCareerTrajectory3D(props: CareerTrajectory3DProps) {
  return (
    <Suspense
      fallback={
        <section
          className="flex min-h-64 items-center justify-center rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500"
          aria-label="Loading career map"
        >
          Preparing your career map…
        </section>
      }
    >
      <CareerTrajectory3D {...props} />
    </Suspense>
  )
}
