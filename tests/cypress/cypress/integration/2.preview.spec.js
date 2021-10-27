/// <reference types="cypress" />

const csvfiles = require('../fixtures/csvfiles')

describe('Preview of .csv files', () => {
  before(() => {
    cy.visit('http://127.0.0.1:8000')
  })
  it('Does not render preview div on initial page load', () => {
    cy.get('#preview').should('not.exist')
  })
  it('Warns user if no usable data is found in file', () => {

  })
  csvfiles.valid.forEach((csvfile) => {
    describe(`File: ${csvfile.filename}`, () => {
      before(() => {
        cy.get('#uploaded-files-select')
          .select(csvfile.filename)
      })
      it('Shows preview upon selection in dropdown', () => {
        cy.get('#preview')
          .should('exist')
      })
      it('Shows filename', () => {
        cy.get('#csv-filename')
          .should('have.text', `File: ${csvfile.filename}`)
      })
      it('Shows total and excluded row counts', () => {
        cy.get('#csv-row-count')
          .should('have.text',
            `${csvfile.preview.numRows} rows, ${csvfile.preview.numDiscarded} excluded`
          )
      })
      it('Shows viable column count', () => {
        cy.get('#csv-viable-column-count')
          .should('have.text',
            `${csvfile.preview.viableColumnIndices.length} viable columns detected`)
      })
      describe('Preview data table', () => {
        it('Has correct structure', () => {
          cy.get('#preview-table')
            .within(() => {
              cy.get('tr')
                .should('have.length', 6)
                .children()
                .should('have.length', 6 * csvfile.preview.previewData[0].length)
              cy.get('thead')
                .should('have.length', 1)
            })
        })
        it('Has correct data', () => {
          cy.get('#preview-table')
            .find('tr')
            .each(($tr, rowIndex, $list) => {
              const row = csvfile.preview.previewData[rowIndex]
              cy.wrap($tr)
                .children()
                .each(($el, colIndex, $list) => {
                  cy.wrap($el)
                    .should('have.text', row[colIndex])
                })
            })
        })
        describe('Headers/named columns can be toggled on/off', () => {
          function testHeadersOn () {
            const viableColumnNames = csvfile.preview.viableColumnIndices.map(
              (columnIndex) => csvfile.preview.previewData[0][columnIndex]
            )
            it('Parses first row of .csv as headers in preview table', () => {
              cy.get('#preview-table')
                .within(() => {
                  // F
                  cy.get('tr').first()
                    .children('th')
                    .each(($th, index, $list) => {
                      cy.wrap($th)
                        .should('have.text', csvfile.preview.previewData[0][index])
                    })
                })
            })
            it('Uses column names as option text in column dropdown', () => {
              cy.get('#csv-target-column-select')
                .find('option')
                .each(($option, index, $options) => {
                  cy.wrap($option)
                    .should('have.text', viableColumnNames[index])
                })
            })
          }

          function testHeadersOff () {
            it('Parses first row of .csv as data in preview table', () => {
              cy.get('#preview-table')
                .within(() => {
                  cy.get('tr').first()
                    .children('th')
                    .each(($th, index, $list) => {
                      // Now each column is called #1, #2, etc.
                      cy.wrap($th)
                        .should('have.text', '#' + (index + 1))
                    })
                })
            })
            it('Uses column indices as option text in column dropdown', () => {
              cy.get('#csv-target-column-select')
                .find('option')
                .each(($option, index, $options) => {
                  cy.wrap($option)
                    .should('have.text', '#' + (csvfile.preview.viableColumnIndices[index] + 1))
                })
            })
          }

          it('Parses first row as headers by default', () => {
            testHeadersOn()
          })
          it('Stops parsing first row as headers after toggle button clicked', () => {
            cy.get('#csv-has-headers-input').click()
            testHeadersOff()
          })
          it('Resumes default behavior after toggle button clicked again', () => {
            cy.get('#csv-has-headers-input').click()
            testHeadersOn()
          })
        })
      })
    })
  })
})




