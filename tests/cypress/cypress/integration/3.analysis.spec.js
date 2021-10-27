/// <reference types="cypress" />

const csvfiles = require('../fixtures/csvfiles')

function forEachCSVFileIt (desc, test) {
  it(desc, () => {
    csvfiles.valid.forEach((csvfile) => {
      cy.get('#uploaded-files-select')
        .select(csvfile.filename)
      test(csvfile)
    })
  })
}

function forEachColumnIt (desc, test) {
  it(desc, () => {
    csvfiles.valid.forEach((csvfile) => {
      cy.get('#uploaded-files-select')
        .select(csvfile.filename)
      csvfile.analysis.forEach((column, index) => {
        cy.get('#csv-target-column-select')
          .select(index)
        test(column, index, csvfile)
      })
    })
  })
}

function forAllPValuesIt (desc, test) {
  it(desc, () => {
    csvfiles.valid.forEach((csvfile) => {
      cy.get('#uploaded-files-select')
        .select(csvfile.filename)
      csvfile.analysis.forEach((column, index) => {
        cy.get('#csv-target-column-select')
          .select(index)
        const pValues = Object.keys(column.criticalValues)
        pValues.forEach((pValue) => {
          cy.get('#test-p-value-select')
            .select(pValue)
          test(pValue, column)
        })
      })
    })
  })
}

describe('Statistical analysis', () => {
  before(() => {
    cy.visit('http://127.0.0.1:8000/clear')
    cy.visit('http://127.0.0.1:8000')
    csvfiles.valid.forEach((csvfile) => {
      cy.get('#upload-file')
        .attachFile({ filePath: `../fixtures/${csvfile.filename}`, fileName: csvfile.filename })
    })
  })
  it('Does not render analysis div on initial page load', () => {
    cy.get('#analysis').should('not.exist')
  })
  forEachCSVFileIt('Shows viable columns in dropdown', (csvfile) => {
    csvfile.analysis.forEach((column, index) => {
      cy.get('#csv-target-column-select')
        .find('option')
        .eq(index)
        .should('contain.text', column.name)
    })
  })
  describe('Has expected layout', () => {
    before(() => {
      cy.get('#uploaded-files-select')
        .select(csvfiles.valid[0].filename)
      cy.get('#csv-target-column-select')
        .select(0)
    })

    it('Renders analysis div on column selection', () => {
      cy.get('#analysis')
        .should('exist')
    })

    it('Has correct title', () => {
      cy.get('#analysis')
        .get('h2.h3.card-title')
        .should('contain.text', 'Analysis')
    })

    it('Shows histogram', () => {
      cy.get('#histogram')
        .find('canvas')
        .should('exist')
    })

    it('Shows digit frequency table with expected layout', () => {
      cy.get('#frequencies')
        .find('h4.h5.card-title')
        .should('contain.text', 'Distribution of digits')

      cy.get('#frequencies-table')
        .find('tr')
        .should('have.length', 3)
        .each(($tr, index, $list) => {
          cy.wrap($tr).children()
            .should('have.length', 10)
        })

      cy.get('#frequencies-table').within(() => {
        cy.get('tr').should('have.length', 3)
        cy.get('tr').eq(0)
          .find('th')
          .each(($th, index, $list) => {
            if (index === 0) {
              cy.wrap($th).should('contain.text', ' ')
            } else {
              cy.wrap($th).should('contain.text', index)
            }
          })
        cy.get('tr').eq(1)
          .find('th')
          .should('contain.text', 'Expected')

        cy.get('tr').eq(2)
          .find('th')
          .should('contain.text', 'Observed')
      })
    })

    it('Shows goodness-of-fit section with expected layout', () => {
      cy.get('#goodness-of-fit-test')
        .prev('h2.h4.card-title')
        .should('contain.text', 'Goodness-of-fit test')
      cy.get('#goodness-of-fit-test')
        .within(() => {
          const headingNames = [
            'Sample size:',
            'p-value',
            'Critical value:',
            'Null hypothesis (H0):',
            'Test statistic:',
            'Result:',
            'Interpretation:',
            'Conclusion:',
          ]
          cy.get('dt').each(($dt, index, $list) => {
            cy.wrap($dt)
              .should('contain.text', headingNames[index])
            cy.wrap($dt).next()
              .should('match', 'dd')
          })
        })
    })
  })

  describe('Frequency table shows accurate data', () => {
    forEachColumnIt('Displays expected distribution', (column, index) => {
      cy.get('#frequencies-table').within(() => {
        cy.get('tr').eq(1)
          .find('td')
          .each(($td, index, $list) => {
            const expectedCount = column.expectedDistribution[index + 1]
            cy.wrap($td).should('contain.text', expectedCount.toFixed(0))
          })
      })
    })

    forEachColumnIt('Displays observed distribution', (column) => {
      cy.get('#frequencies-table').within(() => {
        cy.get('tr').eq(2)
          .find('td')
          .each(($td, index, $list) => {
            cy.wrap($td).should('contain.text', column.observedDistribution[index + 1])
          })
      })
    })
  })

  describe('Goodness-of-fit section shows accurate data', () => {
    forEachColumnIt('Displays sample size and excluded rows', (column, index, csvfile) => {
      cy.get('#test-sample-size')
        .should('contain.text',
          `n = ${column.n} (${csvfile.preview.numRows - column.n} rows excluded)`
        )
    })

    forEachColumnIt('Has correct p-value options in dropdown', (column) => {
      cy.get('#test-p-value-select')
        .find('option')
        .should('have.length', 5)
        .each(($option, index, options) => {
          cy.wrap($option)
            .should('contain.text', Object.keys(column.criticalValues)[index])
        })
    })

    forAllPValuesIt('Displays critical value', (pValue, column) => {
      cy.get('#test-critical-value')
        .should('contain.text', `(p = ${pValue}) χ²c = ${column.criticalValues[pValue]}`)
    })

    forEachColumnIt('Displays test statistic', (column) => {
      cy.get('#test-statistic')
        .should('contain.text',
          `χ² (8, N=${column.n}) = ${column.testStatistic.toPrecision(6)}`
        )
    })

    forAllPValuesIt('Displays test result', (pValue, column) => {
      cy.get('#test-result')
        .should('contain.text',
          column.goodnessOfFit[pValue]
            ? 'χ² > χ²c'
            : 'χ² < χ²c'
        )
    })

    forAllPValuesIt('Displays interpretation', (pValue, column) => {
      cy.get('#test-interpretation')
        .should('contain.text',
          column.goodnessOfFit[pValue]
            ? `Reject the null hypothesis; significant differences between distributions at p = ${pValue}.`
            : `Retain the null hypothesis; no significant differences between distributions at p = ${pValue}.`
        )
    })

    forAllPValuesIt('Displays conclusion', (pValue, column) => {
      cy.get('#test-conclusion')
        .should('contain.text',
          column.goodnessOfFit[pValue]
            ? 'Observed distribution does not conform to Benford\'s Law.'
            : 'Observed distribution conforms to Benford\'s Law.'
        )
    })
  })
})
