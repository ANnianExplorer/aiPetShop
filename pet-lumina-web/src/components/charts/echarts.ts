import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart, GraphChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, PieChart, BarChart, GraphChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

export const theme = {
  primary: '#6daf92',
  primaryDark: '#266a51',
  secondary: '#3a6758',
  palette: ['#6daf92', '#91d4b6', '#bcedda', '#3a6758', '#266a51', '#aa9ead'],
  fontFamily: 'Plus Jakarta Sans',
  bodyFont: 'Noto Sans SC',
  textColor: '#404944',
  splitLine: 'rgba(255,255,255,0.2)',
  tooltip: {
    backgroundColor: 'rgba(255,255,255,0.9)',
    borderColor: 'rgba(109,175,146,0.2)',
    borderRadius: 12,
    textStyle: { fontFamily: 'Plus Jakarta Sans' },
  },
}
