import React, { useState } from 'react'
import { Search, MapPin, Loader } from 'lucide-react'

interface ParcelSearchProps {
  onSearch: (cadastralNumber: string) => void
  isLoading: boolean
  defaultCadastralNumber?: string
}

export function ParcelSearch({ onSearch, isLoading, defaultCadastralNumber }: ParcelSearchProps) {
  const [cadastralNumber, setCadastralNumber] = useState(defaultCadastralNumber || '')
  const [isValid, setIsValid] = useState(true)

  const validateCadastralNumber = (value: string): boolean => {
    // Проверка формата кадастрового номера: XX:XX:XXXXXXX:XXX
    const pattern = /^\d{2}:\d{2}:\d{7}:\d{1,4}$/
    return pattern.test(value)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!cadastralNumber.trim()) {
      setIsValid(false)
      return
    }

    if (!validateCadastralNumber(cadastralNumber)) {
      setIsValid(false)
      return
    }

    setIsValid(true)
    onSearch(cadastralNumber)
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center mb-6">
        <MapPin className="w-8 h-8 text-blue-600 mr-3" />
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Поиск земельного участка</h2>
          <p className="text-gray-600">Введите кадастровый номер для поиска участка</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="cadastralNumber" className="block text-sm font-medium text-gray-700 mb-2">
            Кадастровый номер
          </label>
          <div className="relative">
            <input
              type="text"
              id="cadastralNumber"
              value={cadastralNumber}
              onChange={(e) => {
                setCadastralNumber(e.target.value)
                setIsValid(true)
              }}
              placeholder="78:12:0000101:123"
              className={`w-full px-4 py-3 pr-12 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                isValid ? 'border-gray-300' : 'border-red-500 ring-red-200'
              }`}
              disabled={isLoading}
            />
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
          </div>
          {!isValid && (
            <p className="mt-2 text-sm text-red-600">
              Пожалуйста, введите корректный кадастровый номер в формате XX:XX:XXXXXXX:XXX
            </p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Пример: 78:12:0000101:123
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">Что мы найдем</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Адрес и местоположение</li>
              <li>• Площадь участка</li>
              <li>• Категорию земли</li>
              <li>• Целевое назначение</li>
            </ul>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-900 mb-2">Как использовать</h3>
            <ol className="text-sm text-green-800 space-y-1">
              <li>1. Введите кадастровый номер</li>
              <li>2. Нажмите "Найти участок"</li>
              <li>3. Проверьте найденные данные</li>
              <li>4. Перейдите к оценке</li>
            </ol>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h3 className="font-semibold text-purple-900 mb-2">Где найти номер</h3>
            <p className="text-sm text-purple-800">
              Кадастровый номер указан в:
              • Свидетельстве о праве собственности
              • Кадастровом паспорте
              • Выписке из ЕГРН
            </p>
          </div>
        </div>

        <div className="flex justify-between items-center pt-4">
          <div className="text-sm text-gray-600">
            Нужна помощь? Обратитесь в поддержку
          </div>
          <button
            type="submit"
            disabled={isLoading || !cadastralNumber.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center space-x-2"
          >
            {isLoading ? (
              <>
                <Loader className="animate-spin h-5 w-5" />
                <span>Поиск...</span>
              </>
            ) : (
              <>
                <Search className="h-5 w-5" />
                <span>Найти участок</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}