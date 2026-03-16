import Head from 'next/head'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import toast from 'react-hot-toast'

// Компоненты
import { ParcelSearch } from '@/components/ParcelSearch'
import { EvaluationForm } from '@/components/EvaluationForm'
import { ResultsDisplay } from '@/components/ResultsDisplay'
import { MarketAnalytics } from '@/components/MarketAnalytics'

// Типы данных
interface ParcelData {
  cadastralNumber: string
  address: string
  area: number
  category: string
  purpose: string
  coordinates: [number, number]
}

interface EvaluationResult {
  id: string
  liquidityScore: number
  confidence: number
  factors: Array<{
    factor: string
    impact: number
    description: string
  }>
  comparableSales: Array<{
    price: number
    area: number
    pricePerSqMeter: number
    distance: number
    date: string
  }>
  recommendations: string[]
}

// Схема валидации
const evaluationSchema = z.object({
  cadastralNumber: z.string().min(1, 'Введите кадастровый номер'),
  address: z.string().min(1, 'Введите адрес'),
  area: z.number().positive('Площадь должна быть положительной'),
  category: z.string().min(1, 'Выберите категорию'),
  purpose: z.string().min(1, 'Выберите целевое назначение'),
})

type EvaluationFormData = z.infer<typeof evaluationSchema>

export default function Home() {
  const [currentStep, setCurrentStep] = useState<'search' | 'evaluation' | 'results'>('search')
  const [parcelData, setParcelData] = useState<ParcelData | null>(null)
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<EvaluationFormData>({
    resolver: zodResolver(evaluationSchema),
  })

  const watchedCadastralNumber = watch('cadastralNumber')

  // Поиск участка
  const handleParcelSearch = async (cadastralNumber: string) => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/parcels/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cadastralNumber }),
      })

      if (!response.ok) {
        throw new Error('Не удалось найти участок')
      }

      const data = await response.json()
      
      // Заполняем форму данными участка
      setValue('cadastralNumber', data.cadastralNumber)
      setValue('address', data.address)
      setValue('area', data.area)
      setValue('category', data.category)
      setValue('purpose', data.purpose)
      
      setParcelData(data)
      setCurrentStep('evaluation')
      toast.success('Участок найден!')
    } catch (error) {
      toast.error('Участок не найден. Проверьте кадастровый номер.')
    } finally {
      setIsLoading(false)
    }
  }

  // Оценка ликвидности
  const onSubmit = async (data: EvaluationFormData) => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Ошибка при оценке ликвидности')
      }

      const result = await response.json()
      setEvaluationResult(result)
      setCurrentStep('results')
      toast.success('Оценка завершена!')
    } catch (error) {
      toast.error('Ошибка при оценке. Попробуйте позже.')
    } finally {
      setIsLoading(false)
    }
  }

  // Сброс оценки
  const resetEvaluation = () => {
    setParcelData(null)
    setEvaluationResult(null)
    setCurrentStep('search')
    setValue('cadastralNumber', '')
    setValue('address', '')
    setValue('area', 0)
    setValue('category', '')
    setValue('purpose', '')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Оценка ликвидности земельных участков</title>
        <meta name="description" content="Система оценки ликвидности земельных участков" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-8">
        {/* Заголовок */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Оценка ликвидности земельных участков
          </h1>
          <p className="text-lg text-gray-600">
            AI-система для автоматической оценки рыночной ликвидности и стоимости земельных участков
          </p>
        </div>

        {/* Прогресс бар */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Шаг 1</span>
            <span className="text-sm font-medium text-gray-700">Шаг 2</span>
            <span className="text-sm font-medium text-gray-700">Шаг 3</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{
                width:
                  currentStep === 'search'
                    ? '33%'
                    : currentStep === 'evaluation'
                    ? '66%'
                    : '100%',
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Поиск участка</span>
            <span>Оценка</span>
            <span>Результаты</span>
          </div>
        </div>

        {/* Контент */}
        <div className="max-w-4xl mx-auto">
          {currentStep === 'search' && (
            <ParcelSearch
              onSearch={handleParcelSearch}
              isLoading={isLoading}
              defaultCadastralNumber={watchedCadastralNumber}
            />
          )}

          {currentStep === 'evaluation' && parcelData && (
            <EvaluationForm
              parcelData={parcelData}
              onSubmit={handleSubmit(onSubmit)}
              isLoading={isLoading}
              onBack={() => setCurrentStep('search')}
            />
          )}

          {currentStep === 'results' && evaluationResult && (
            <ResultsDisplay
              result={evaluationResult}
              onNewEvaluation={resetEvaluation}
            />
          )}
        </div>

        {/* Аналитика рынка */}
        <div className="max-w-6xl mx-auto mt-12">
          <MarketAnalytics />
        </div>
      </main>
    </div>
  )
}