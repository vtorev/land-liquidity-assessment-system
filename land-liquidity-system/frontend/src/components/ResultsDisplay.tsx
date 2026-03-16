import React from 'react'
import { 
  Download, 
  Share2, 
  TrendingUp, 
  Map, 
  BarChart3, 
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react'

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

interface ResultsDisplayProps {
  result: EvaluationResult
  onNewEvaluation: () => void
}

export function ResultsDisplay({ result, onNewEvaluation }: ResultsDisplayProps) {
  const getLiquidityStatus = (score: number) => {
    if (score >= 80) return { label: 'Высокая', color: 'text-green-600', bg: 'bg-green-100' }
    if (score >= 60) return { label: 'Средняя', color: 'text-yellow-600', bg: 'bg-yellow-100' }
    if (score >= 40) return { label: 'Ниже среднего', color: 'text-orange-600', bg: 'bg-orange-100' }
    return { label: 'Низкая', color: 'text-red-600', bg: 'bg-red-100' }
  }

  const status = getLiquidityStatus(result.liquidityScore)

  return (
    <div className="space-y-6">
      {/* Заголовок и действия */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Результаты оценки</h2>
            <p className="text-gray-600">Ликвидность земельного участка</p>
          </div>
          <div className="flex space-x-3">
            <button className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <Download className="h-4 w-4" />
              <span>Скачать PDF</span>
            </button>
            <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              <Share2 className="h-4 w-4" />
              <span>Поделиться</span>
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span>• ID оценки: {result.id}</span>
          <span>• Дата: {new Date().toLocaleDateString('ru-RU')}</span>
          <span>• Доверие: {result.confidence}%</span>
        </div>
      </div>

      {/* Основной результат */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ликвидность */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <TrendingUp className="h-8 w-8 text-blue-600" />
              <div>
                <h3 className="font-semibold text-gray-900">Ликвидность</h3>
                <p className="text-sm text-gray-600">Рыночная способность</p>
              </div>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${status.bg} ${status.color}`}>
              {status.label}
            </div>
          </div>
          
          <div className="text-4xl font-bold text-gray-900 mb-2">{result.liquidityScore}%</div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div 
              className="bg-blue-600 h-4 rounded-full transition-all duration-500"
              style={{ width: `${result.liquidityScore}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-2">
            {result.liquidityScore >= 80 
              ? 'Отличная ликвидность. Участок легко реализуется по рыночной цене.'
              : result.liquidityScore >= 60
              ? 'Хорошая ликвидность. Участок реализуется в разумные сроки.'
              : result.liquidityScore >= 40
              ? 'Умеренная ликвидность. Требуется больше времени для продажи.'
              : 'Низкая ликвидность. Сложности с реализацией по рыночной цене.'
            }
          </p>
        </div>

        {/* Факторы влияния */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <BarChart3 className="h-8 w-8 text-purple-600" />
            <div>
              <h3 className="font-semibold text-gray-900">Ключевые факторы</h3>
              <p className="text-sm text-gray-600">Влияние на ликвидность</p>
            </div>
          </div>
          
          <div className="space-y-3">
            {result.factors.slice(0, 3).map((factor, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900">{factor.factor}</span>
                  <p className="text-xs text-gray-600">{factor.description}</p>
                </div>
                <div className={`text-sm font-semibold ${
                  factor.impact > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {factor.impact > 0 ? '+' : ''}{factor.impact}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Рекомендации */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <AlertCircle className="h-8 w-8 text-orange-600" />
            <div>
              <h3 className="font-semibold text-gray-900">Рекомендации</h3>
              <p className="text-sm text-gray-600">Для повышения ликвидности</p>
            </div>
          </div>
          
          <div className="space-y-3">
            {result.recommendations.slice(0, 3).map((recommendation, index) => (
              <div key={index} className="flex items-start space-x-3">
                <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-700">{recommendation}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Сопоставимые продажи */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Map className="h-8 w-8 text-green-600" />
            <div>
              <h3 className="font-semibold text-gray-900">Сопоставимые продажи</h3>
              <p className="text-sm text-gray-600">Анализ рыночных цен</p>
            </div>
          </div>
          <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            Показать на карте
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-gray-900">Цена</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Площадь</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Цена/м²</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Расстояние</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Дата</th>
              </tr>
            </thead>
            <tbody>
              {result.comparableSales.map((sale, index) => (
                <tr key={index} className="border-b border-gray-100">
                  <td className="py-3 px-4 font-medium">{sale.price.toLocaleString()} ₽</td>
                  <td className="py-3 px-4">{sale.area} м²</td>
                  <td className="py-3 px-4">{sale.pricePerSqMeter.toLocaleString()} ₽/м²</td>
                  <td className="py-3 px-4">{sale.distance} м</td>
                  <td className="py-3 px-4">{sale.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Детальный анализ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Все факторы */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Все факторы влияния</h3>
          <div className="space-y-4">
            {result.factors.map((factor, index) => (
              <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900">{factor.factor}</span>
                  <p className="text-sm text-gray-600 mt-1">{factor.description}</p>
                </div>
                <div className={`text-lg font-bold ${
                  factor.impact > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {factor.impact > 0 ? '+' : ''}{factor.impact}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Полные рекомендации */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Полные рекомендации</h3>
          <div className="space-y-4">
            {result.recommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
                <Clock className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-700">{recommendation}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Кнопки управления */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-600">
            <p>• Результаты основаны на AI-анализе рыночных данных</p>
            <p>• Для уточнения результатов обратитесь к специалисту</p>
          </div>
          <button
            onClick={onNewEvaluation}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            Новая оценка
          </button>
        </div>
      </div>
    </div>
  )
}