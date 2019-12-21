activeCoverAmount = undefined
activeCoverAmountPerContract = undefined
activeCoverAmountByExpirationDate = undefined
allCovers = undefined

const renderActiveCoverAmount = (currency) => {
  if (activeCoverAmount !== undefined) {
    Plotly.newPlot('activeCoverAmount', [{
      x: getDateTimesInLocalTimezone(Object.keys(activeCoverAmount[currency])),
      y: Object.values(activeCoverAmount[currency]),
      fill: 'tozeroy',
      type: 'scatter'
    }])
  }
}

$.get('active_cover_amount', (response) => {
  activeCoverAmount = response
  renderActiveCoverAmount('USD')
})

$('#active-cover-amount-usd').click(() => {
  renderActiveCoverAmount('USD')
})

$('#active-cover-amount-eth').click(() => {
  renderActiveCoverAmount('ETH')
})

const renderActiveCoverAmountPerContract = (currency) => {
  if (activeCoverAmountPerContract !== undefined) {
    Plotly.newPlot('activeCoverAmountPerContract', [{
      x: Object.keys(activeCoverAmountPerContract[currency]),
      y: Object.values(activeCoverAmountPerContract[currency]),
      type: 'bar'
    }])
  }
}

$.get('active_cover_amount_per_contract', (response) => {
  activeCoverAmountPerContract = response
  renderActiveCoverAmountPerContract('USD')
})

$('#active-cover-amount-per-contract-usd').click(() => {
  renderActiveCoverAmountPerContract('USD')
})

$('#active-cover-amount-per-contract-eth').click(() => {
  renderActiveCoverAmountPerContract('ETH')
})

const renderActiveCoverAmountByExpirationDate = (currency) => {
  if (activeCoverAmountByExpirationDate !== undefined) {
    Plotly.newPlot('activeCoverAmountByExpirationDate', [{
      x: Object.keys(activeCoverAmountByExpirationDate[currency]),
      y: Object.values(activeCoverAmountByExpirationDate[currency]),
      type: 'bar'
    }])
  }
}

$.get('active_cover_amount_by_expiration_date', (response) => {
  activeCoverAmountByExpirationDate = response
  renderActiveCoverAmountByExpirationDate('USD')
})

$('#active-cover-amount-by-expiration-date-usd').click(() => {
  renderActiveCoverAmountByExpirationDate('USD')
})

$('#active-cover-amount-by-expiration-date-eth').click(() => {
  renderActiveCoverAmountByExpirationDate('ETH')
})

const renderAllCovers = (currency) => {
  if (allCovers !== undefined) {
    table = $('#coverDataTable').DataTable()
    table.clear()
    for (cover of allCovers) {
      coverAmount = 0
      premium = 0
      if (currency === 'USD') {
        coverAmount = '$' + cover['amount_usd'].toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
        premium = '$' + cover['premium_usd'].toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
      } else {
        coverAmount = cover['amount'].toLocaleString() + ' ' + cover['currency']
        premium = cover['premium'].toLocaleString() + ' ' + cover['currency']
      }

      table.row.add([
        cover['cover_id'],
        cover['contract_name'],
        coverAmount,
        premium,
        toLocalTimezone(cover['start_time']),
        toLocalTimezone(cover['end_time'])
      ])
    }
    table.draw()
  }
}

$.get('all_covers', (response) => {
  allCovers = response
  renderAllCovers('USD')
})

$('#all-covers-usd').click(() => {
  renderAllCovers('USD')
})

$('#all-covers-eth-dai').click(() => {
  renderAllCovers('ETH/DAI')
})
