public void deleteEmailRecords(List<BatchInternalEmailEntity> entities){
    String query1 = "DELETE FROM ESCON_BATCH_EMAIL_DETAIL WHERE INTERNAL_BATCH_ID IN (SELECT I.INTERNAL_BATCH_ID FROM ESCON_INTERNAL_EMAIL I, ESCON_BATCH_EMAIL_DETAIL D WHERE I.INTERNAL_BATCH_ID = D.INTERNAL_BATCH_ID AND I.PROCESSED_DATE IS NOT NULL;)";
    String query2 = "DELETE FROM ESCON_INTERNAL_EMAIL WHERE PROCESSED_DATE IS NOT NULL;";

    Map<String, Object>[] batchOfInputs = new Hashmap[entities.size()];
    AtomicInteger count = new AtomicInteger();
    entities.forEach(entity -> {
        Map<String, Object> map = new Hashmap();
        map.put("id", entity.getInternalBatchId());
        batchOfInputs[count.getAndIncrement()] = map;
    });
    updateEntities(query1, batchOfInputs);
    updateEntities(query2, batchOfInputs);
}

private void updateEntities(String query, Map<String, Object>[] batchOfInputs){
    int[] updateStatus;
    try {
        updateStatus = namedParameterJdbcTemplate.batchUpdate(query, batchOfInputs);
    } catch(DataAccessException dataAccessException){
        // Insert logging
        throw new ServiceException("Error during bulk update");
    }
}

// ___________________________________________________________________________________________________

// Example test cases for a similar function.

@Test
public void updateAllEmailEntitiesTest_Success() throws ServiceException {
    List<BatchInternalEmailEntity> entities = new ArrayList<>();
    BatchInternalEmailEntity entity = new BatchInternalEmailEntity();
    entity.setInternalbatchId(123);
    entity.setProcessedDate(LocalDateTime.now());
    entities.add(entity);
    when(namedParameterJdbcTemplate.batchUpdate(Mockito.anyString(), Mockito.any(map[].class))).thenReturn(new int[]{1});
    repo.updateAllEmailEntities(entities);
    verify(namedParameterJdbcTemplate, tinmes(1)).batchUpdate(Mockito.anyString(), Mockito.any(map[].class));
}

@Test
public void updateAllEmailEntitiesTest_Exception() throws ServiceException {
    Asserts.assertThrows(ServiceException.class, () -> {
        List<BatchInternalEmailEntity> entities = new ArrayList<>();
        BatchInternalEmailEntity entity = new BatchInternalEmailEntity();
        entity.setInternalbatchId(123);
        entity.setProcessedDate(LocalDateTime.now());
        entities.add(entity);
        when(namedParameterJdbcTemplate.batchUpdate(Mockito.anyString(), Mockito.any(map[].class))).thenThrow(Mockito.mock(DataAccessException.class));
        repo.updateAllEmailEntities(entities);
    })
}