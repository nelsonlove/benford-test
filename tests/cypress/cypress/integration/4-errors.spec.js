/// <reference types="cypress" />

const csvfiles = require('../fixtures/csvfiles')

describe('File upload errors', () => {
  beforeEach(() => {
    cy.visit('http://127.0.0.1:8000')
  })

  it('Warns user on attempted upload of file with duplicate name', () => {
    const duplicate = csvfiles.valid[0]
    cy.get('#upload-file-input')
      .attachFile({ filePath: `../fixtures/${duplicate.filename}`, fileName: duplicate.filename })
    cy.get('#upload-error')
      .should('have.text', 'Error: An uploaded file with that name already exists.')
  })

  it('Warns user on attempted upload of non-.csv file', () => {
    const bad_file = csvfiles.invalid.badFile
    cy.get('#upload-file-input')
      .attachFile({ filePath: `../fixtures/${bad_file.filename}`, fileName: bad_file.filename })
    cy.get('#upload-error')
      .should('have.text', 'Error: This file could not be parsed as a .csv.')
  })
})

describe('Preview errors', () => {
  it('Warns user if file has no viable columns', () => {
    const no_columns = csvfiles.invalid.allBadColumns
    cy.get('#upload-file-input')
      .attachFile({ filePath: `../fixtures/${no_columns.filename}`, fileName: no_columns.filename })
    cy.get('#preview-error')
      .should('have.text', 'Warning: No usable data was found. Please ensure the file has at least one column which is unambiguously numerical.')
  })
})

describe('Analysis errors', () => {
  it('Warns user if selected column has >10% bad data', () => {
    const bad_column = csvfiles.invalid.oneBadColumn
    cy.get('#upload-file-input')
      .attachFile({ filePath: `../fixtures/${bad_column.filename}`, fileName: bad_column.filename })
    cy.get('#csv-target-column-select')
      .select('bad_column')
    cy.get('#analysis-error')
      .should('have.text', 'Note: no numerical data was found for 10% or more of rows in the target column. These rows are not included in the analysis.')
  })
})