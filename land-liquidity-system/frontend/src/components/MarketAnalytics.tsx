import React from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  MapPin, 
  BarChart3, 
  Users,
  Calendar
} from 'lucide-react'

interface MarketAnalyticsProps {}

export function MarketAnalytics({}: MarketAnalyticsProps) {
  // Данные для аналитики (в реальной системе будут из API)
  const marketData = {
    averagePrice: 52000,
    priceChange: 12.5,
    transactionsCount: 156,
    activeListings: 842,
    averageLiquidity: 68.3,
    topLocations: [
      { name: 'Центральный район', count: 124, avgPrice: 75000 },
      { name: 'Красносельский район', count: 89, avgPrice: 45000 },
      { name: 'Адмиралтейский район', count: 67, avgPrice: 82000 },
      { name: 'Петроградский район', count: 54, avgPrice: 58000 },
    ],
    priceTrends: [
      { month: 'Янв', price: 48000 },
      { month: 'Фев', price: 49500 },
      { month: 'Мар', price: 51000 },
      { month: 'Апр', price: 52500 },
      { month: 'Май', price: 54000 },
      { month: 'Июн', price: 52000 },
    ]
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Рыночная аналитика</h2>
        <p className="text-gray-600 mb-6">
          Комплексный анализ рынка земельных участков в реальном времени
        </p>

        {/* Основные метрики */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <DollarSign className="h-8 w-8 text-blue-600" />
              <span className="text-sm text-blue-600 font-medium">Средняя цена</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {marketData.averagePrice.toLocaleString()} ₽/м²
            </div>
            <div className="flex items-center mt-2 text-green-600">
              <TrendingUp className="h-4 w-4 mr-1" />
              <span className="text-sm font-medium">+{marketData.priceChange}%</span>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <Users className="h-8 w-8 text-green-600" />
              <span className="text-sm text-green-600 font-medium">Сделки</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {marketData.transactionsCount}
            </div>
            <div className="text-sm text-gray-600 mt-2">за месяц</div>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <MapPin className="h-8 w-8 text-purple-600" />
              <span className="text-sm text-purple-600 font-medium">Объекты</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {marketData.activeListings}
            </div>
            <div className="text-sm text-gray-600 mt-2">в продаже</div>
          </div>

          <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <BarChart3 className="h-8 w-8 text-orange-600" />
              <span className="text-sm text-orange-600 font-medium">Ликвидность</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {marketData.averageLiquidity}%
            </div>
            <div className="text-sm text-gray-600 mt-2">средняя</div>
          </div>
        </div>

        {/* Тренды цен */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Динамика цен</h3>
              <Calendar className="h-5 w-5 text-gray-600" />
            </div>
            <div className="space-y-3">
              {marketData.priceTrends.map((trend, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{trend.month}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">{trend.price.toLocaleString()} ₽</span>
                    {index > 0 && (
                      <span className={`text-xs ${
                        trend.price > marketData.priceTrends[index - 1].price 
                          ? 'text-green-600' 
                          : 'text-red-600'
                      }`}>
                        {trend.price > marketData.priceTrends[index - 1].price ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Топ локаций */}
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Топ локаций</h3>
              <MapPin className="h-5 w-5 text-gray-600" />
            </div>
            <div className="space-y-4">
              {marketData.topLocations.map((location, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg">
                  <div>
                    <span className="font-medium text-gray-900">{location.name}</span>
                    <p className="text-xs text-gray-600">{location.count} участков</p>
                  </div>
                  <div className="text-right">
                    <span className="font-semibold">{location.avgPrice.toLocaleString()} ₽/м²</span>
                    <div className="w-16 bg-gray-200 rounded-full h-2 mt-1">
                      <div 
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${(location.avgPrice / 85000) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Рекомендации */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Рыночные рекомендации</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="font-medium mb-1">• Продажа</p>
              <p className="opacity-90">Сейчас благоприятное время для продажи участков в центральных районах</p>
            </div>
            <div>
              <p className="font-medium mb-1">• Покупка</p>
              <p className="opacity-90">Наибольшая выгода при покупке в пригородных зонах с развитой инфраструктурой</p>
            </div>
            <div>
              <p className="font-medium mb-1">• Инвестиции</p>
              <p className="opacity-90">Перспективные направления: новые жилые комплексы и бизнес-парки</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}