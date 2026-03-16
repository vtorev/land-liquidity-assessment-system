import React from 'react'
import { ArrowLeft, Save, FileText } from 'lucide-react'

interface ParcelData {
  cadastralNumber: string
  address: string
  area: number
  category: string
  purpose: string
  coordinates: [number, number]
}

interface EvaluationFormProps {
  parcelData: ParcelData
  onSubmit: (e: React.FormEvent) => void
  isLoading: boolean
  onBack: () => void
}

export function EvaluationForm({ parcelData, onSubmit, isLoading, onBack }: EvaluationFormProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <button
            onClick={onBack}
            className="mr-4 p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Оценка ликвидности</h2>
            <p className="text-gray-600">Анализ участка и расчет рыночной стоимости</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Шаг 2 из 3</p>
        </div>
      </div>

      <form onSubmit={onSubmit} className="space-y-6">
        {/* Информация об участке */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Информация об участке</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Кадастровый номер:</span>
              <p className="font-medium">{parcelData.cadastralNumber}</p>
            </div>
            <div>
              <span className="text-gray-500">Адрес:</span>
              <p className="font-medium">{parcelData.address}</p>
            </div>
            <div>
              <span className="text-gray-500">Площадь:</span>
              <p className="font-medium">{parcelData.area} м²</p>
            </div>
            <div>
              <span className="text-gray-500">Категория:</span>
              <p className="font-medium">{parcelData.category}</p>
            </div>
            <div>
              <span className="text-gray-500">Назначение:</span>
              <p className="font-medium">{parcelData.purpose}</p>
            </div>
            <div>
              <span className="text-gray-500">Координаты:</span>
              <p className="font-medium">
                {parcelData.coordinates[0].toFixed(6)}, {parcelData.coordinates[1].toFixed(6)}
              </p>
            </div>
          </div>
        </div>

        {/* Дополнительные параметры */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Дата оценки
            </label>
            <input
              type="date"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Цель оценки
            </label>
            <select className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all">
              <option value="sale">Продажа</option>
              <option value="mortgage">Ипотека</option>
              <option value="inheritance">Наследство</option>
              <option value="tax">Налоговая отчетность</option>
              <option value="other">Другое</option>
            </select>
          </div>
        </div>

        {/* Выбор методов оценки */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Методы оценки
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="flex items-center space-x-3 p-4 border border-gray-300 rounded-lg hover:border-blue-400 transition-colors cursor-pointer">
              <input type="checkbox" defaultChecked className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
              <div>
                <span className="font-medium">Сравнительный</span>
                <p className="text-xs text-gray-500">По сопоставимым продажам</p>
              </div>
            </label>

            <label className="flex items-center space-x-3 p-4 border border-gray-300 rounded-lg hover:border-blue-400 transition-colors cursor-pointer">
              <input type="checkbox" defaultChecked className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
              <div>
                <span className="font-medium">Доходный</span>
                <p className="text-xs text-gray-500">По доходности участка</p>
              </div>
            </label>

            <label className="flex items-center space-x-3 p-4 border border-gray-300 rounded-lg hover:border-blue-400 transition-colors cursor-pointer">
              <input type="checkbox" className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
              <div>
                <span className="font-medium">Затратный</span>
                <p className="text-xs text-gray-500">По восстановительной стоимости</p>
              </div>
            </label>
          </div>
        </div>

        {/* Особые условия */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Особые условия
          </label>
          <textarea
            rows={4}
            placeholder="Опишите особые условия, ограничения или преимущества участка..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
          />
          <p className="mt-1 text-xs text-gray-500">
            Укажите наличие коммуникаций, обременений, экологические особенности и т.д.
          </p>
        </div>

        {/* Кнопки управления */}
        <div className="flex justify-between items-center pt-4 border-t">
          <div className="text-sm text-gray-600">
            <p>• Все данные будут проанализированы с использованием AI</p>
            <p>• Результаты будут доступны через несколько минут</p>
          </div>
          
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onBack}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Назад
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Оценка...</span>
                </>
              ) : (
                <>
                  <FileText className="h-5 w-5" />
                  <span>Начать оценку</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}